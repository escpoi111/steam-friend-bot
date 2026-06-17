#!/usr/bin/env python3
"""本地配置解析工具。"""

import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONFIG_PATH = "steam_friend_bot.local.json"
DEFAULT_DELAY_SECONDS = "5"
DEFAULT_FRIEND_CODES_FILE = "friend_codes.txt"
DEFAULT_EXCLUDE_FILE = "exclude_list.txt"

FIELD_ALIASES = {
    "api_key": ("api_key", "steam_api_key", "STEAM_API_KEY"),
    "steam_id": ("steam_id", "steamid", "STEAM_ID"),
    "session_id": ("session_id", "steam_session_id", "STEAM_SESSION_ID"),
    "cookies": ("cookies", "steam_cookies", "STEAM_COOKIES"),
    "add_delay_seconds": (
        "add_delay_seconds",
        "delay",
        "ADD_DELAY_SECONDS",
    ),
    "friend_codes_file": (
        "friend_codes_file",
        "codes_file",
        "FRIEND_CODES_FILE",
    ),
    "exclude_file": ("exclude_file", "EXCLUDE_FILE"),
}

ENV_VAR_MAP = {
    "api_key": "STEAM_API_KEY",
    "steam_id": "STEAM_ID",
    "session_id": "STEAM_SESSION_ID",
    "cookies": "STEAM_COOKIES",
    "add_delay_seconds": "ADD_DELAY_SECONDS",
    "friend_codes_file": "FRIEND_CODES_FILE",
    "exclude_file": "EXCLUDE_FILE",
}


def parse_cookies(cookies_str: str) -> Dict[str, str]:
    """解析 cookies 字符串为字典。"""
    cookie_dict = {}
    for item in cookies_str.split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            cookie_dict[key.strip()] = value.strip()
    return cookie_dict


def _normalize_cookies(cookies_str: str, session_id: str) -> str:
    """标准化 cookies，并以单独配置的 Session ID 为准。"""
    cookie_dict = parse_cookies(cookies_str)
    if session_id:
        cookie_dict["sessionid"] = session_id
    return "; ".join(f"{key}={value}" for key, value in cookie_dict.items())


def _read_json_config(path: str) -> Tuple[Dict[str, str], Optional[str]]:
    """读取 JSON 配置文件。"""
    if not path or not os.path.exists(path):
        return {}, None

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"无法读取本地配置文件 {path}: {exc}"

    if not isinstance(raw_data, dict):
        return {}, f"本地配置文件 {path} 的内容必须是 JSON 对象"

    normalized = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            value = raw_data.get(alias)
            if value is not None:
                normalized[field] = str(value).strip()
                break
    return normalized, None


@dataclass
class ResolvedSteamConfig:
    """统一后的 Steam 本地配置。"""

    api_key: str = ""
    steam_id: str = ""
    session_id: str = ""
    cookies: str = ""
    add_delay_seconds: str = DEFAULT_DELAY_SECONDS
    friend_codes_file: str = DEFAULT_FRIEND_CODES_FILE
    exclude_file: str = DEFAULT_EXCLUDE_FILE
    config_path: str = DEFAULT_CONFIG_PATH
    config_file_found: bool = False

    def to_dict(self, mask_secrets: bool = False) -> Dict[str, str]:
        """返回适合 GUI/CLI 使用的配置字典。"""
        data = {
            "api_key": self.api_key,
            "steam_id": self.steam_id,
            "session_id": self.session_id,
            "cookies": self.cookies,
            "add_delay_seconds": self.add_delay_seconds,
            "friend_codes_file": self.friend_codes_file,
            "exclude_file": self.exclude_file,
            "config_path": self.config_path,
        }
        if mask_secrets:
            data["api_key"] = _mask_secret(data["api_key"])
            data["session_id"] = _mask_secret(data["session_id"])
            data["cookies"] = _mask_secret(data["cookies"])
        return data

    @property
    def delay_seconds(self) -> float:
        """获取数字形式的延迟秒数。"""
        return float(self.add_delay_seconds)


def _mask_secret(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def resolve_steam_config(
    overrides: Optional[Mapping[str, str]] = None,
) -> Tuple[ResolvedSteamConfig, List[str]]:
    """从 JSON、本地环境变量和手动覆盖项解析配置。"""
    config_path = os.getenv("STEAM_CONFIG_PATH", DEFAULT_CONFIG_PATH)
    file_values, file_error = _read_json_config(config_path)

    resolved = dict(file_values)
    for field, env_name in ENV_VAR_MAP.items():
        value = os.getenv(env_name)
        if value is not None and value.strip():
            resolved[field] = value.strip()

    if overrides:
        for field, value in overrides.items():
            if value is None:
                continue
            text = str(value).strip()
            if text:
                resolved[field] = text

    config = ResolvedSteamConfig(
        api_key=resolved.get("api_key", ""),
        steam_id=resolved.get("steam_id", ""),
        session_id=resolved.get("session_id", ""),
        cookies=resolved.get("cookies", ""),
        add_delay_seconds=resolved.get(
            "add_delay_seconds", DEFAULT_DELAY_SECONDS
        ),
        friend_codes_file=resolved.get(
            "friend_codes_file", DEFAULT_FRIEND_CODES_FILE
        ),
        exclude_file=resolved.get("exclude_file", DEFAULT_EXCLUDE_FILE),
        config_path=config_path,
        config_file_found=os.path.exists(config_path),
    )

    if config.cookies:
        config.cookies = _normalize_cookies(config.cookies, config.session_id)

    errors = validate_steam_config(config)
    if file_error:
        errors.insert(0, file_error)
    return config, errors


def validate_steam_config(config: ResolvedSteamConfig) -> List[str]:
    """校验统一后的本地配置。"""
    errors = []

    if not config.api_key:
        errors.append(
            "缺少 Steam API Key，请在 .env、环境变量或本地 JSON 中设置 STEAM_API_KEY / api_key"
        )
    elif not re.fullmatch(r"[A-Fa-f0-9]{32}", config.api_key):
        errors.append("Steam API Key 格式无效，应为 32 位十六进制字符串")

    if not config.steam_id:
        errors.append(
            "缺少 SteamID64，请在 .env、环境变量或本地 JSON 中设置 STEAM_ID / steam_id"
        )
    elif not re.fullmatch(r"7656\d{13}", config.steam_id):
        errors.append("SteamID64 格式无效，应为 17 位且以 7656 开头")

    if not config.session_id:
        errors.append(
            "缺少 Session ID，请在 .env、环境变量或本地 JSON 中设置 STEAM_SESSION_ID / session_id"
        )

    if not config.cookies:
        errors.append(
            "缺少 Cookies，请在 .env、环境变量或本地 JSON 中设置 STEAM_COOKIES / cookies"
        )
    else:
        parsed = parse_cookies(config.cookies)
        if not parsed:
            errors.append("Cookies 格式无效，应为 key=value; key2=value2")
        elif "steamLoginSecure" not in parsed:
            errors.append("Cookies 缺少 steamLoginSecure，无法复用本地登录态")

    try:
        delay = float(config.add_delay_seconds)
        if delay <= 0:
            errors.append("添加间隔必须大于 0 秒")
    except ValueError:
        errors.append("添加间隔必须是数字")

    return errors
