#!/usr/bin/env python3
"""
Steam 自动加好友程序
-------------------
支持导入多个 Steam 好友代码，自动发送好友请求。
可通过排除列表选择哪些好友不需要添加。

用法:
    python steam_friend_bot.py
"""

import os
import sys
import time
import logging
import requests
from typing import List, Set
from steam_local_config import parse_cookies, resolve_steam_config

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("steam_friend_bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# Steam 好友代码与 SteamID64 之间的转换
STEAM_BASE_ID = 76561197960265728


def friend_code_to_steam_id(friend_code: str) -> str:
    """将 Steam 好友代码转换为 SteamID64。

    Steam 好友代码是基于账号 ID 的编码。
    好友代码去掉分隔符后为纯数字，其值等于账号 ID。
    SteamID64 = 账号 ID + 76561197960265728
    """
    code = friend_code.strip().replace("-", "").replace(" ", "")
    if not code.isdigit():
        raise ValueError(f"无效的好友代码: {friend_code}")
    account_id = int(code)
    steam_id64 = account_id + STEAM_BASE_ID
    return str(steam_id64)


def steam_id_to_friend_code(steam_id64: str) -> str:
    """将 SteamID64 转换为好友代码。"""
    account_id = int(steam_id64) - STEAM_BASE_ID
    return str(account_id)


def load_friend_codes(file_path: str) -> List[str]:
    """从文件中加载好友代码列表。

    支持的格式:
    - 每行一个好友代码
    - 支持带分隔符的格式 (如 1234-5678-9012)
    - 支持纯数字格式
    - 支持 SteamID64 格式 (17位数字)
    - 忽略空行和 # 开头的注释行
    """
    codes = []
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return codes

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            codes.append(line)
            logger.debug(f"读取第 {line_num} 行: {line}")

    logger.info(f"从 {file_path} 加载了 {len(codes)} 个好友代码")
    return codes


def load_exclude_list(file_path: str) -> Set[str]:
    """从文件中加载排除列表（不需要添加的好友代码）。

    格式与好友代码文件相同。
    """
    excludes = set()
    if not os.path.exists(file_path):
        logger.info(f"排除列表文件不存在: {file_path}，将不排除任何好友")
        return excludes

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            excludes.add(line)

    logger.info(f"从 {file_path} 加载了 {len(excludes)} 个排除项")
    return excludes


def normalize_code(code: str) -> str:
    """标准化好友代码，去除分隔符和空格，用于比较。"""
    return code.strip().replace("-", "").replace(" ", "")


def resolve_to_steam_id(code: str) -> str:
    """将好友代码或 SteamID64 解析为 SteamID64。

    如果输入是17位数字且以7656开头，视为 SteamID64 直接返回。
    否则视为好友代码进行转换。
    """
    normalized = normalize_code(code)
    if len(normalized) == 17 and normalized.startswith("7656"):
        return normalized
    return friend_code_to_steam_id(code)


class SteamFriendBot:
    """Steam 自动加好友机器人。"""

    INVITE_FRIEND_URL = "https://api.steampowered.com/ISteamUser/AddFriend/v1"
    PLAYER_SUMMARIES_URL = (
        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2"
    )
    FRIEND_LIST_URL = "https://api.steampowered.com/ISteamUser/GetFriendList/v1"

    def __init__(
        self,
        api_key: str,
        steam_id: str,
        session_id: str,
        cookies: str,
        delay_seconds: float = 5,
    ):
        """初始化机器人。

        Args:
            api_key: Steam Web API 密钥
            steam_id: 自己的 SteamID64
            session_id: Steam 登录后的 sessionid
            cookies: Steam 登录后的 cookies 字符串
        """
        self.api_key = api_key
        self.steam_id = steam_id
        self.session_id = session_id
        self.cookies = parse_cookies(cookies)
        self.delay = delay_seconds

    def get_existing_friends(self) -> Set[str]:
        """获取当前好友列表。"""
        try:
            resp = requests.get(
                self.FRIEND_LIST_URL,
                params={"key": self.api_key, "steamid": self.steam_id},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            friends = data.get("friendslist", {}).get("friends", [])
            friend_ids = {f["steamid"] for f in friends}
            logger.info(f"当前已有 {len(friend_ids)} 个好友")
            return friend_ids
        except requests.RequestException as e:
            logger.warning(f"获取好友列表失败: {e}")
            return set()

    def get_player_name(self, steam_id: str) -> str:
        """获取玩家昵称。"""
        try:
            resp = requests.get(
                self.PLAYER_SUMMARIES_URL,
                params={"key": self.api_key, "steamids": steam_id},
                timeout=10,
            )
            resp.raise_for_status()
            players = resp.json().get("response", {}).get("players", [])
            if players:
                return players[0].get("personaname", "未知")
        except requests.RequestException:
            pass
        return "未知"

    def add_friend(self, target_steam_id: str) -> bool:
        """向目标用户发送好友请求。

        使用 Steam 社区的 AJAX 接口添加好友。

        Args:
            target_steam_id: 目标用户的 SteamID64

        Returns:
            是否发送成功
        """
        url = f"https://steamcommunity.com/actions/AddFriendAjax"
        data = {
            "sessionID": self.session_id,
            "steamid": target_steam_id,
            "accept_invite": 0,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://steamcommunity.com/profiles/{target_steam_id}",
        }

        try:
            resp = requests.post(
                url,
                data=data,
                headers=headers,
                cookies=self.cookies,
                timeout=15,
            )
            if resp.status_code == 200:
                result = resp.json() if resp.text else {}
                if result.get("invited") or result.get("success") == 1:
                    return True
                else:
                    logger.warning(
                        f"添加好友响应异常: {resp.text}"
                    )
                    return False
            else:
                logger.warning(
                    f"添加好友请求失败，状态码: {resp.status_code}"
                )
                return False
        except requests.RequestException as e:
            logger.error(f"添加好友请求异常: {e}")
            return False

    def run(
        self,
        friend_codes_file: str = "friend_codes.txt",
        exclude_file: str = "exclude_list.txt",
    ):
        """运行自动加好友流程。

        Args:
            friend_codes_file: 好友代码文件路径
            exclude_file: 排除列表文件路径
        """
        logger.info("=" * 50)
        logger.info("Steam 自动加好友程序启动")
        logger.info("=" * 50)

        # 加载好友代码
        friend_codes = load_friend_codes(friend_codes_file)
        if not friend_codes:
            logger.error("没有找到需要添加的好友代码，请检查文件")
            return

        # 加载排除列表
        exclude_set = load_exclude_list(exclude_file)

        # 获取当前好友列表
        existing_friends = self.get_existing_friends()

        # 处理每个好友代码
        success_count = 0
        skip_count = 0
        fail_count = 0

        for code in friend_codes:
            normalized = normalize_code(code)

            # 检查是否在排除列表中
            is_excluded = False
            for exc in exclude_set:
                if normalize_code(exc) == normalized:
                    is_excluded = True
                    break

            if is_excluded:
                logger.info(f"[跳过-排除] {code} (在排除列表中)")
                skip_count += 1
                continue

            # 解析为 SteamID64
            try:
                target_id = resolve_to_steam_id(code)
            except ValueError as e:
                logger.error(f"[错误] {code}: {e}")
                fail_count += 1
                continue

            # 检查是否已是好友
            if target_id in existing_friends:
                logger.info(f"[跳过-已好友] {code} (SteamID: {target_id})")
                skip_count += 1
                continue

            # 检查是否是自己
            if target_id == self.steam_id:
                logger.info(f"[跳过] {code} (这是自己的账号)")
                skip_count += 1
                continue

            # 获取玩家名称
            player_name = self.get_player_name(target_id)

            # 发送好友请求
            logger.info(f"[添加中] {code} -> {player_name} (SteamID: {target_id})")
            if self.add_friend(target_id):
                logger.info(f"[成功] 已向 {player_name} 发送好友请求")
                success_count += 1
            else:
                logger.warning(f"[失败] 向 {player_name} 发送好友请求失败")
                fail_count += 1

            # 请求间延迟，避免触发限制
            time.sleep(self.delay)

        # 输出统计
        logger.info("=" * 50)
        logger.info("执行完成!")
        logger.info(f"  成功: {success_count}")
        logger.info(f"  跳过: {skip_count}")
        logger.info(f"  失败: {fail_count}")
        logger.info(f"  总计: {len(friend_codes)}")
        logger.info("=" * 50)


def main():
    """主函数。"""
    config, errors = resolve_steam_config()
    if errors:
        logger.error("本地 Steam 配置无效，请检查以下项目:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error(
            "请参考 .env.example，或在本地配置文件中填写 %s",
            config.config_path,
        )
        sys.exit(1)

    # 创建机器人并运行
    bot = SteamFriendBot(
        api_key=config.api_key,
        steam_id=config.steam_id,
        session_id=config.session_id,
        cookies=config.cookies,
        delay_seconds=config.delay_seconds,
    )
    bot.run(
        friend_codes_file=config.friend_codes_file,
        exclude_file=config.exclude_file,
    )


if __name__ == "__main__":
    main()
