#!/usr/bin/env python3
"""
Steam 自动加好友程序 - 图形界面版
==================================
傻瓜式操作界面，支持:
- 粘贴浏览器 Cookies 自动提取配置（用户只需填 API Key）
- 好友代码列表带勾选框，可选择哪些添加
- 排除列表带勾选框
- 自动查询并显示 SteamID64、昵称、主页链接
- 一键开始添加好友
- 实时查看运行日志

可用 PyInstaller 打包为 exe:
    pyinstaller --onefile --windowed --name SteamFriendBot steam_friend_bot_gui.py
"""

import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import webbrowser
import requests
from typing import List, Set, Dict, Optional
from urllib.parse import unquote
from steam_local_config import (
    DEFAULT_CONFIG_PATH,
    parse_cookies,
    resolve_steam_config,
)


# ==================== 核心逻辑 ====================

STEAM_BASE_ID = 76561197960265728


def friend_code_to_steam_id(friend_code: str) -> str:
    """将 Steam 好友代码转换为 SteamID64。"""
    code = friend_code.strip().replace("-", "").replace(" ", "")
    if not code.isdigit():
        raise ValueError(f"无效的好友代码: {friend_code}")
    account_id = int(code)
    steam_id64 = account_id + STEAM_BASE_ID
    return str(steam_id64)


def normalize_code(code: str) -> str:
    """标准化好友代码。"""
    return code.strip().replace("-", "").replace(" ", "")


def resolve_to_steam_id(code: str) -> str:
    """将好友代码或 SteamID64 解析为 SteamID64。"""
    normalized = normalize_code(code)
    if len(normalized) == 17 and normalized.startswith("7656"):
        return normalized
    return friend_code_to_steam_id(code)


def extract_steam_id_from_login_secure(login_secure: str) -> str:
    """从 steamLoginSecure 值中提取 SteamID64。

    格式: {steamid}%7C%7C{token} 或 {steamid}||{token}
    """
    decoded = unquote(login_secure)
    if "||" in decoded:
        steam_id = decoded.split("||")[0]
        if steam_id.isdigit() and len(steam_id) == 17:
            return steam_id
    return ""


# ==================== GUI 应用 ====================


class SteamFriendBotGUI:
    """Steam 自动加好友 - 图形界面。"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Steam 自动加好友工具")
        self.root.geometry("900x800")
        self.root.resizable(True, True)

        # 状态
        self.is_running = False
        self.stop_flag = False
        self.friend_codes_file = ""
        self.exclude_file = ""
        # 好友代码数据: {code: {"checked": BooleanVar, "steam_id": str, "name": str}}
        self.codes_data: Dict[str, dict] = {}
        # 排除列表数据
        self.exclude_data: Dict[str, dict] = {}

        self._build_ui()
        self._load_local_config(initial=True)

    def _build_ui(self):
        """构建界面。"""
        # 主框架 - 使用 notebook 分标签页
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== 配置区域 =====
        config_frame = ttk.LabelFrame(main_frame, text="Steam 配置", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # API Key
        ttk.Label(config_frame, text="API Key:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(
            config_frame, textvariable=self.api_key_var, width=60, show="*"
        )
        self.api_key_entry.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0))

        # 浏览器 Cookies 输入
        ttk.Label(config_frame, text="浏览器Cookies:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        cookie_input_frame = ttk.Frame(config_frame)
        cookie_input_frame.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.browser_cookies_var = tk.StringVar()
        self.browser_cookies_entry = ttk.Entry(
            cookie_input_frame, textvariable=self.browser_cookies_var, width=45, show="*"
        )
        self.browser_cookies_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            cookie_input_frame, text="解析Cookies", command=self._parse_browser_cookies
        ).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(
            config_frame,
            text="从浏览器开发者工具复制完整 Cookie 字符串粘贴于此，点击解析自动提取 Session ID、SteamID 和 steamLoginSecure",
        ).grid(row=2, column=1, sticky=tk.W, pady=(0, 4), padx=(5, 0))

        # Steam ID (auto-filled)
        ttk.Label(config_frame, text="你的SteamID64:").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self.steam_id_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.steam_id_var, width=60).grid(
            row=3, column=1, sticky=tk.EW, pady=2, padx=(5, 0)
        )

        # Session ID (auto-filled)
        ttk.Label(config_frame, text="Session ID:").grid(
            row=4, column=0, sticky=tk.W, pady=2
        )
        self.session_id_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.session_id_var, width=60).grid(
            row=4, column=1, sticky=tk.EW, pady=2, padx=(5, 0)
        )

        # steamLoginSecure (auto-filled)
        ttk.Label(config_frame, text="steamLoginSecure:").grid(
            row=5, column=0, sticky=tk.W, pady=2
        )
        self.cookies_var = tk.StringVar()
        ttk.Entry(
            config_frame, textvariable=self.cookies_var, width=60, show="*"
        ).grid(row=5, column=1, sticky=tk.EW, pady=2, padx=(5, 0))

        # 延迟
        ttk.Label(config_frame, text="添加间隔(秒):").grid(
            row=6, column=0, sticky=tk.W, pady=2
        )
        self.delay_var = tk.StringVar(value="5")
        ttk.Entry(config_frame, textvariable=self.delay_var, width=10).grid(
            row=6, column=1, sticky=tk.W, pady=2, padx=(5, 0)
        )

        config_button_row = ttk.Frame(config_frame)
        config_button_row.grid(row=7, column=1, sticky=tk.W, pady=(4, 0), padx=(5, 0))
        ttk.Button(
            config_button_row,
            text="从本地配置加载",
            command=self._load_local_config,
        ).pack(side=tk.LEFT, padx=(0, 8))
        self.config_status_var = tk.StringVar(value="未加载本地配置")
        ttk.Label(config_button_row, textvariable=self.config_status_var).pack(
            side=tk.LEFT
        )

        config_frame.columnconfigure(1, weight=1)

        # ===== 好友代码区域 (Treeview with checkboxes) =====
        codes_frame = ttk.LabelFrame(main_frame, text="好友代码列表", padding=10)
        codes_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 按钮行
        btn_row = ttk.Frame(codes_frame)
        btn_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(btn_row, text="从文件导入", command=self._import_codes).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(btn_row, text="手动添加", command=self._add_code_dialog).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(btn_row, text="查询信息", command=self._resolve_all_codes).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(btn_row, text="全选", command=self._select_all_codes).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(btn_row, text="全不选", command=self._deselect_all_codes).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(btn_row, text="删除选中", command=self._delete_selected_codes).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.code_count_label = ttk.Label(btn_row, text="共 0 个")
        self.code_count_label.pack(side=tk.RIGHT)

        # Treeview
        codes_tree_frame = ttk.Frame(codes_frame)
        codes_tree_frame.pack(fill=tk.BOTH, expand=True)

        self.codes_tree = ttk.Treeview(
            codes_tree_frame,
            columns=("checked", "code", "steam_id", "name", "profile"),
            show="headings",
            selectmode="extended",
        )
        self.codes_tree.heading("checked", text="✓")
        self.codes_tree.heading("code", text="好友代码")
        self.codes_tree.heading("steam_id", text="SteamID64")
        self.codes_tree.heading("name", text="昵称")
        self.codes_tree.heading("profile", text="主页")

        self.codes_tree.column("checked", width=30, anchor=tk.CENTER)
        self.codes_tree.column("code", width=120)
        self.codes_tree.column("steam_id", width=160)
        self.codes_tree.column("name", width=150)
        self.codes_tree.column("profile", width=250)

        codes_scrollbar = ttk.Scrollbar(
            codes_tree_frame, orient=tk.VERTICAL, command=self.codes_tree.yview
        )
        self.codes_tree.configure(yscrollcommand=codes_scrollbar.set)
        self.codes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        codes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 点击切换勾选 / 双击打开主页
        self.codes_tree.bind("<Button-1>", self._on_codes_tree_click)
        self.codes_tree.bind("<Double-1>", self._on_codes_tree_double_click)

        # ===== 排除列表区域 =====
        exclude_frame = ttk.LabelFrame(
            main_frame, text="排除列表 - 勾选的项不会被添加", padding=10
        )
        exclude_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))

        exc_btn_row = ttk.Frame(exclude_frame)
        exc_btn_row.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(exc_btn_row, text="从文件导入", command=self._import_excludes).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(exc_btn_row, text="手动添加", command=self._add_exclude_dialog).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(exc_btn_row, text="全选", command=self._select_all_excludes).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(exc_btn_row, text="全不选", command=self._deselect_all_excludes).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(exc_btn_row, text="删除选中", command=self._delete_selected_excludes).pack(
            side=tk.LEFT, padx=(0, 5)
        )

        # Treeview for excludes
        exclude_tree_frame = ttk.Frame(exclude_frame)
        exclude_tree_frame.pack(fill=tk.BOTH, expand=True)

        self.exclude_tree = ttk.Treeview(
            exclude_tree_frame,
            columns=("checked", "code", "steam_id", "name"),
            show="headings",
            height=4,
        )
        self.exclude_tree.heading("checked", text="✓")
        self.exclude_tree.heading("code", text="好友代码/ID")
        self.exclude_tree.heading("steam_id", text="SteamID64")
        self.exclude_tree.heading("name", text="昵称")

        self.exclude_tree.column("checked", width=30, anchor=tk.CENTER)
        self.exclude_tree.column("code", width=120)
        self.exclude_tree.column("steam_id", width=160)
        self.exclude_tree.column("name", width=150)

        exc_scrollbar = ttk.Scrollbar(
            exclude_tree_frame, orient=tk.VERTICAL, command=self.exclude_tree.yview
        )
        self.exclude_tree.configure(yscrollcommand=exc_scrollbar.set)
        self.exclude_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        exc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.exclude_tree.bind("<Button-1>", self._on_exclude_tree_click)

        # ===== 操作按钮 =====
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(
            action_frame,
            text="🚀 开始添加好友",
            command=self._start,
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(
            action_frame, text="⏹ 停止", command=self._stop, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)

        self.status_label = ttk.Label(action_frame, text="就绪", foreground="green")
        self.status_label.pack(side=tk.RIGHT)

        # ===== 日志区域 =====
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=6, width=60, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ==================== Cookie 解析 ====================

    def _parse_browser_cookies(self):
        """从粘贴的浏览器 Cookie 字符串中自动提取配置。"""
        raw_cookies = self.browser_cookies_var.get().strip()
        if not raw_cookies:
            messagebox.showwarning("提示", "请先粘贴浏览器的 Cookie 字符串")
            return

        parsed = parse_cookies(raw_cookies)

        # Extract sessionid
        if "sessionid" in parsed:
            self.session_id_var.set(parsed["sessionid"])
            self._log("✅ 已提取 Session ID")

        # Extract steamLoginSecure
        if "steamLoginSecure" in parsed:
            login_secure = parsed["steamLoginSecure"]
            self.cookies_var.set(login_secure)
            self._log("✅ 已提取 steamLoginSecure")

            # Extract SteamID64 from steamLoginSecure
            steam_id = extract_steam_id_from_login_secure(login_secure)
            if steam_id:
                self.steam_id_var.set(steam_id)
                self._log(f"✅ 已提取 SteamID64: {steam_id}")
            else:
                self._log("⚠️ 无法从 steamLoginSecure 中提取 SteamID64，请手动填写")
        else:
            self._log("⚠️ Cookie 中未找到 steamLoginSecure")

        if "sessionid" not in parsed and "steamLoginSecure" not in parsed:
            messagebox.showwarning(
                "解析失败",
                "未能从粘贴的内容中找到有效的 Steam Cookie。\n"
                "请确保从浏览器开发者工具中复制完整的 Cookie 字符串。",
            )
        else:
            self._save_local_config()
            self._log("配置已自动保存")

    # ==================== Treeview 勾选操作 ====================

    def _toggle_tree_check(self, tree, item):
        """切换 Treeview 某行的勾选状态。"""
        values = list(tree.item(item, "values"))
        if values[0] == "☑":
            values[0] = "☐"
        else:
            values[0] = "☑"
        tree.item(item, values=values)

    def _on_codes_tree_click(self, event):
        """点击好友代码列表切换勾选。"""
        region = self.codes_tree.identify("region", event.x, event.y)
        if region == "cell":
            col = self.codes_tree.identify_column(event.x)
            item = self.codes_tree.identify_row(event.y)
            if item and col == "#1":  # checked column
                self._toggle_tree_check(self.codes_tree, item)

    def _on_codes_tree_double_click(self, event):
        """双击好友代码列表打开主页。"""
        region = self.codes_tree.identify("region", event.x, event.y)
        if region == "cell":
            col = self.codes_tree.identify_column(event.x)
            item = self.codes_tree.identify_row(event.y)
            if item and col == "#5":  # profile column
                values = self.codes_tree.item(item, "values")
                if len(values) >= 5 and values[4]:
                    webbrowser.open(values[4])

    def _on_exclude_tree_click(self, event):
        """点击排除列表切换勾选。"""
        region = self.exclude_tree.identify("region", event.x, event.y)
        if region == "cell":
            col = self.exclude_tree.identify_column(event.x)
            item = self.exclude_tree.identify_row(event.y)
            if item and col == "#1":  # checked column
                self._toggle_tree_check(self.exclude_tree, item)

    # ==================== 好友代码操作 ====================

    def _add_code_to_tree(self, code: str, checked: bool = True,
                          steam_id: str = "", name: str = "", profile: str = ""):
        """向好友代码 Treeview 添加一行。"""
        check_mark = "☑" if checked else "☐"
        self.codes_tree.insert(
            "", tk.END,
            values=(check_mark, code, steam_id, name, profile)
        )
        self._update_code_count()

    def _add_code_dialog(self):
        """弹窗手动添加好友代码。"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加好友代码")
        dialog.geometry("400x200")
        dialog.transient(self.root)

        ttk.Label(dialog, text="输入好友代码（每行一个）:").pack(
            pady=(10, 5), padx=10, anchor=tk.W
        )
        text = scrolledtext.ScrolledText(dialog, height=5, width=40)
        text.pack(fill=tk.BOTH, expand=True, padx=10)

        def on_ok():
            for line in text.get("1.0", tk.END).splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    self._add_code_to_tree(line)
            dialog.destroy()

        ttk.Button(dialog, text="确定", command=on_ok).pack(pady=10)

    def _import_codes(self):
        """从文件导入好友代码。"""
        file_path = filedialog.askopenfilename(
            title="选择好友代码文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self._add_code_to_tree(line)
            self._log(f"已从文件导入: {file_path}")

    def _select_all_codes(self):
        """全选好友代码。"""
        for item in self.codes_tree.get_children():
            values = list(self.codes_tree.item(item, "values"))
            values[0] = "☑"
            self.codes_tree.item(item, values=values)

    def _deselect_all_codes(self):
        """全不选好友代码。"""
        for item in self.codes_tree.get_children():
            values = list(self.codes_tree.item(item, "values"))
            values[0] = "☐"
            self.codes_tree.item(item, values=values)

    def _delete_selected_codes(self):
        """删除 Treeview 中选中的行。"""
        selected = self.codes_tree.selection()
        if not selected:
            # Delete unchecked items
            to_delete = []
            for item in self.codes_tree.get_children():
                values = self.codes_tree.item(item, "values")
                if values[0] == "☐":
                    to_delete.append(item)
            for item in to_delete:
                self.codes_tree.delete(item)
        else:
            for item in selected:
                self.codes_tree.delete(item)
        self._update_code_count()

    def _update_code_count(self, event=None):
        """更新好友代码计数。"""
        total = len(self.codes_tree.get_children())
        checked = sum(
            1 for item in self.codes_tree.get_children()
            if self.codes_tree.item(item, "values")[0] == "☑"
        )
        self.code_count_label.config(text=f"共 {total} 个，已选 {checked} 个")

    def _resolve_all_codes(self):
        """在后台线程中查询所有好友代码的 SteamID64 和昵称。"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("提示", "请先填写 API Key")
            return

        items = self.codes_tree.get_children()
        if not items:
            messagebox.showinfo("提示", "好友代码列表为空")
            return

        self._log("正在查询好友信息...")
        thread = threading.Thread(
            target=self._resolve_codes_thread, args=(api_key,), daemon=True
        )
        thread.start()

    def _resolve_codes_thread(self, api_key: str):
        """后台查询好友代码信息。"""
        items = self.codes_tree.get_children()
        # Collect steam_ids to query in batches
        item_steamids = []
        for item in items:
            values = self.codes_tree.item(item, "values")
            code = values[1]
            try:
                steam_id = resolve_to_steam_id(code)
            except ValueError:
                steam_id = ""
            item_steamids.append((item, code, steam_id))

        # Batch query player names (Steam API supports up to 100 per call)
        all_steam_ids = [sid for _, _, sid in item_steamids if sid]
        player_info = {}

        for i in range(0, len(all_steam_ids), 100):
            batch = all_steam_ids[i:i + 100]
            try:
                resp = requests.get(
                    "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2",
                    params={"key": api_key, "steamids": ",".join(batch)},
                    timeout=15,
                )
                if resp.status_code == 200:
                    players = resp.json().get("response", {}).get("players", [])
                    for p in players:
                        player_info[p["steamid"]] = p.get("personaname", "未知")
            except Exception as e:
                self._log(f"⚠️ 查询玩家信息失败: {e}")

        # Update treeview in main thread
        def update_ui():
            for item, code, steam_id in item_steamids:
                if not steam_id:
                    values = list(self.codes_tree.item(item, "values"))
                    values[2] = "无效代码"
                    self.codes_tree.item(item, values=values)
                    continue
                name = player_info.get(steam_id, "未知")
                profile = f"https://steamcommunity.com/profiles/{steam_id}"
                values = list(self.codes_tree.item(item, "values"))
                values[2] = steam_id
                values[3] = name
                values[4] = profile
                self.codes_tree.item(item, values=values)
            self._log(f"✅ 已查询 {len(item_steamids)} 个好友信息")

        self.root.after(0, update_ui)

    # ==================== 排除列表操作 ====================

    def _add_exclude_to_tree(self, code: str, checked: bool = True,
                             steam_id: str = "", name: str = ""):
        """向排除列表 Treeview 添加一行。"""
        check_mark = "☑" if checked else "☐"
        self.exclude_tree.insert(
            "", tk.END,
            values=(check_mark, code, steam_id, name)
        )

    def _add_exclude_dialog(self):
        """弹窗手动添加排除项。"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加排除项")
        dialog.geometry("400x200")
        dialog.transient(self.root)

        ttk.Label(dialog, text="输入要排除的好友代码（每行一个）:").pack(
            pady=(10, 5), padx=10, anchor=tk.W
        )
        text = scrolledtext.ScrolledText(dialog, height=5, width=40)
        text.pack(fill=tk.BOTH, expand=True, padx=10)

        def on_ok():
            for line in text.get("1.0", tk.END).splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    self._add_exclude_to_tree(line)
            dialog.destroy()

        ttk.Button(dialog, text="确定", command=on_ok).pack(pady=10)

    def _import_excludes(self):
        """从文件导入排除列表。"""
        file_path = filedialog.askopenfilename(
            title="选择排除列表文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        self._add_exclude_to_tree(line)
            self._log(f"已导入排除列表: {file_path}")

    def _select_all_excludes(self):
        """全选排除列表。"""
        for item in self.exclude_tree.get_children():
            values = list(self.exclude_tree.item(item, "values"))
            values[0] = "☑"
            self.exclude_tree.item(item, values=values)

    def _deselect_all_excludes(self):
        """全不选排除列表。"""
        for item in self.exclude_tree.get_children():
            values = list(self.exclude_tree.item(item, "values"))
            values[0] = "☐"
            self.exclude_tree.item(item, values=values)

    def _delete_selected_excludes(self):
        """删除排除列表中选中的行。"""
        selected = self.exclude_tree.selection()
        if not selected:
            to_delete = []
            for item in self.exclude_tree.get_children():
                values = self.exclude_tree.item(item, "values")
                if values[0] == "☐":
                    to_delete.append(item)
            for item in to_delete:
                self.exclude_tree.delete(item)
        else:
            for item in selected:
                self.exclude_tree.delete(item)

    # ==================== 配置相关 ====================

    def _get_config_overrides(self) -> dict:
        cookies_value = self.cookies_var.get().strip()
        # User only fills the value; auto-prepend key if needed
        if cookies_value and "=" not in cookies_value:
            cookies_value = f"steamLoginSecure={cookies_value}"
        elif cookies_value and not cookies_value.startswith("steamLoginSecure="):
            # Already has = but might be just the value with special chars
            if "steamLoginSecure" not in cookies_value:
                cookies_value = f"steamLoginSecure={cookies_value}"
        return {
            "api_key": self.api_key_var.get().strip(),
            "steam_id": self.steam_id_var.get().strip(),
            "session_id": self.session_id_var.get().strip(),
            "cookies": cookies_value,
            "add_delay_seconds": self.delay_var.get().strip(),
        }

    def _load_text_file_to_tree(self, file_path: str, tree_add_func,
                                log_missing: bool = True):
        """从文件加载数据到 Treeview。"""
        if not file_path:
            return
        if not os.path.exists(file_path):
            if log_missing:
                self._log(f"⚠️ 文件不存在: {file_path}")
            return
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    tree_add_func(line)

    def _apply_resolved_config(
        self,
        config,
        log_result: bool = True,
        load_files: bool = True,
        log_missing_files: bool = True,
    ):
        self.api_key_var.set(config.api_key)
        self.steam_id_var.set(config.steam_id)
        self.session_id_var.set(config.session_id)
        # Display only the steamLoginSecure value in the field
        cookies_display = config.cookies
        parsed = parse_cookies(cookies_display)
        if "steamLoginSecure" in parsed:
            cookies_display = parsed["steamLoginSecure"]
        self.cookies_var.set(cookies_display)
        self.delay_var.set(config.add_delay_seconds)
        self.friend_codes_file = config.friend_codes_file
        self.exclude_file = config.exclude_file
        self.config_status_var.set(f"已加载: {config.config_path}")
        if load_files:
            # Clear existing tree data
            for item in self.codes_tree.get_children():
                self.codes_tree.delete(item)
            for item in self.exclude_tree.get_children():
                self.exclude_tree.delete(item)
            self._load_text_file_to_tree(
                config.friend_codes_file,
                self._add_code_to_tree,
                log_missing=log_missing_files,
            )
            self._load_text_file_to_tree(
                config.exclude_file,
                self._add_exclude_to_tree,
                log_missing=log_missing_files,
            )
            self._update_code_count()
        if log_result:
            self._log(f"已加载本地配置: {config.config_path}")

    def _load_local_config(self, initial: bool = False):
        config, errors = resolve_steam_config(overrides=self._get_config_overrides())
        self._apply_resolved_config(
            config,
            log_result=not initial,
            log_missing_files=not initial,
        )
        if errors and not initial:
            messagebox.showwarning("本地配置提示", "\n".join(errors))
        elif initial and not config.config_file_found:
            self.config_status_var.set("使用 .env / 环境变量默认配置")

    def _validate_config(self):
        """验证配置并返回解析后的配置。"""
        config, errors = resolve_steam_config(overrides=self._get_config_overrides())
        if errors:
            messagebox.showerror("错误", "\n".join(errors))
            return None
        self._apply_resolved_config(config, log_result=False, load_files=False)
        self._save_local_config()
        return config

    def _save_local_config(self):
        """自动保存当前 GUI 配置到本地 JSON 文件。"""
        config_path = os.getenv("STEAM_CONFIG_PATH", DEFAULT_CONFIG_PATH)
        # Read existing config to preserve extra fields
        existing = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (OSError, json.JSONDecodeError):
                existing = {}

        cookies_value = self.cookies_var.get().strip()
        # Save the full cookie string with prefix
        if cookies_value and "=" not in cookies_value:
            cookies_value = f"steamLoginSecure={cookies_value}"

        existing["api_key"] = self.api_key_var.get().strip()
        existing["steam_id"] = self.steam_id_var.get().strip()
        existing["session_id"] = self.session_id_var.get().strip()
        existing["cookies"] = cookies_value
        existing["add_delay_seconds"] = int(self.delay_var.get().strip() or "5")

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            self._log(f"配置已自动保存到 {config_path}")
        except OSError as e:
            self._log(f"⚠️ 保存配置失败: {e}")

    # ==================== 运行逻辑 ====================

    def _get_checked_codes(self) -> List[str]:
        """获取勾选的好友代码列表。"""
        codes = []
        for item in self.codes_tree.get_children():
            values = self.codes_tree.item(item, "values")
            if values[0] == "☑":
                codes.append(values[1])
        return codes

    def _get_exclude_set(self) -> Set[str]:
        """获取勾选的排除列表。"""
        excludes = set()
        for item in self.exclude_tree.get_children():
            values = self.exclude_tree.item(item, "values")
            if values[0] == "☑":
                excludes.add(values[1])
        return excludes

    def _start(self):
        """开始添加好友。"""
        config = self._validate_config()
        if not config:
            return

        codes = self._get_checked_codes()
        if not codes:
            messagebox.showerror("错误", "请先勾选要添加的好友代码")
            return

        self.is_running = True
        self.stop_flag = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="运行中...", foreground="blue")

        # 在后台线程运行
        thread = threading.Thread(target=self._run_bot, args=(config,), daemon=True)
        thread.start()

    def _stop(self):
        """停止添加。"""
        self.stop_flag = True
        self._log("正在停止...")

    def _finish(self):
        """运行结束后恢复界面。"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="就绪", foreground="green")

    def _run_bot(self, config):
        """后台线程: 执行添加好友逻辑。"""
        try:
            api_key = config.api_key
            steam_id = config.steam_id
            session_id = config.session_id
            cookies_str = config.cookies
            delay = config.delay_seconds

            cookies = parse_cookies(cookies_str)
            codes = self._get_checked_codes()
            exclude_set = self._get_exclude_set()

            self._log(f"共 {len(codes)} 个好友代码，{len(exclude_set)} 个排除项")
            self._log("正在获取当前好友列表...")

            # 获取已有好友
            existing_friends: Set[str] = set()
            try:
                resp = requests.get(
                    "https://api.steampowered.com/ISteamUser/GetFriendList/v1",
                    params={"key": api_key, "steamid": steam_id},
                    timeout=15,
                )
                resp.raise_for_status()
                friends = resp.json().get("friendslist", {}).get("friends", [])
                existing_friends = {f["steamid"] for f in friends}
                self._log(f"当前已有 {len(existing_friends)} 个好友")
            except Exception as e:
                self._log(f"⚠️ 获取好友列表失败: {e}")

            # 统计
            success_count = 0
            skip_count = 0
            fail_count = 0

            for i, code in enumerate(codes):
                if self.stop_flag:
                    self._log("用户手动停止")
                    break

                normalized = normalize_code(code)

                # 检查排除列表
                is_excluded = any(
                    normalize_code(exc) == normalized for exc in exclude_set
                )
                if is_excluded:
                    self._log(f"[跳过-排除] {code}")
                    skip_count += 1
                    continue

                # 解析 SteamID64
                try:
                    target_id = resolve_to_steam_id(code)
                except ValueError as e:
                    self._log(f"[错误] {code}: {e}")
                    fail_count += 1
                    continue

                # 已是好友
                if target_id in existing_friends:
                    self._log(f"[跳过-已好友] {code}")
                    skip_count += 1
                    continue

                # 自己
                if target_id == steam_id:
                    self._log(f"[跳过] {code} (自己)")
                    skip_count += 1
                    continue

                # 获取昵称
                player_name = "未知"
                try:
                    resp = requests.get(
                        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2",
                        params={"key": api_key, "steamids": target_id},
                        timeout=10,
                    )
                    players = resp.json().get("response", {}).get("players", [])
                    if players:
                        player_name = players[0].get("personaname", "未知")
                except Exception:
                    pass

                # 发送好友请求
                self._log(
                    f"[{i+1}/{len(codes)}] 添加 {player_name} ({target_id})..."
                )

                try:
                    resp = requests.post(
                        "https://steamcommunity.com/actions/AddFriendAjax",
                        data={
                            "sessionID": session_id,
                            "steamid": target_id,
                            "accept_invite": 0,
                        },
                        headers={
                            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                            "X-Requested-With": "XMLHttpRequest",
                            "Referer": f"https://steamcommunity.com/profiles/{target_id}",
                        },
                        cookies=cookies,
                        timeout=15,
                    )
                    if resp.status_code == 200:
                        result = resp.json() if resp.text else {}
                        if result.get("invited") or result.get("success") == 1:
                            self._log(f"  ✅ 成功添加 {player_name}")
                            success_count += 1
                        else:
                            self._log(f"  ❌ 失败: {resp.text}")
                            fail_count += 1
                    else:
                        self._log(f"  ❌ 请求失败 (HTTP {resp.status_code})")
                        fail_count += 1
                except Exception as e:
                    self._log(f"  ❌ 异常: {e}")
                    fail_count += 1

                # 延迟
                if i < len(codes) - 1 and not self.stop_flag:
                    time.sleep(delay)

            # 汇总
            self._log("=" * 40)
            self._log(f"执行完成! 成功:{success_count} 跳过:{skip_count} 失败:{fail_count}")
            self._log("=" * 40)

        except Exception as e:
            self._log(f"运行出错: {e}")

        finally:
            self.root.after(0, self._finish)

    # ==================== 日志 ====================

    def _log(self, msg: str):
        """向日志区域添加消息。"""
        self.root.after(0, self._append_log, msg)

    def _append_log(self, msg: str):
        """在主线程中追加日志。"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def run(self):
        """启动 GUI。"""
        self.root.mainloop()


def main():
    app = SteamFriendBotGUI()
    app.run()


if __name__ == "__main__":
    main()
