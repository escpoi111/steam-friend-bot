"""自动配置导入服务：bootstrap、校验、备份与回滚。"""

import json
import os
import shutil
from copy import deepcopy

import yaml
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
DEFAULT_PATH = os.path.join(CONFIG_DIR, "default.yaml")
RUNTIME_PATH = os.path.join(CONFIG_DIR, "config.yaml")


class ConfigService:
    """管理运行时配置的生命周期：自动创建、读取、校验、导入和回滚。"""

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        load_dotenv()

    # ------------------------------------------------------------------
    # 启动引导
    # ------------------------------------------------------------------

    def bootstrap(self) -> dict:
        """确保运行时配置存在，应用环境变量覆盖，校验并写回。"""
        if not os.path.exists(DEFAULT_PATH):
            self._create_default_file()

        if not os.path.exists(RUNTIME_PATH):
            shutil.copyfile(DEFAULT_PATH, RUNTIME_PATH)

        cfg = self._read_yaml(RUNTIME_PATH)
        cfg = self._apply_env_override(cfg)
        cfg = self.validate_and_fill(cfg)
        self.save_runtime_config(cfg)
        return cfg

    # ------------------------------------------------------------------
    # 内部辅助
    # ------------------------------------------------------------------

    def _create_default_file(self) -> None:
        default_cfg = {
            "server": {"port": 8080},
            "app": {"novice_mode": True, "name": "steam-friend-bot"},
            "phone": {"pattern": r"^1[3-9]\d{9}$"},
        }
        with open(DEFAULT_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(default_cfg, f, allow_unicode=True, sort_keys=False)

    def _read_yaml(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _apply_env_override(self, cfg: dict) -> dict:
        cfg = deepcopy(cfg)
        port = os.getenv("APP_PORT")
        novice = os.getenv("NOVICE_MODE")
        if port and str(port).isdigit():
            cfg.setdefault("server", {})["port"] = int(port)
        if novice is not None:
            cfg.setdefault("app", {})["novice_mode"] = (
                str(novice).lower() in ("1", "true", "yes", "y")
            )
        return cfg

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def validate_and_fill(self, cfg: dict) -> dict:
        """校验配置并自动补全缺失字段，返回合法配置字典。"""
        if not isinstance(cfg, dict):
            raise ValueError("配置必须是字典格式")

        cfg.setdefault("server", {})
        cfg.setdefault("app", {})
        cfg.setdefault("phone", {})

        port = cfg["server"].get("port", 8080)
        if not isinstance(port, int) or not (1 <= port <= 65535):
            cfg["server"]["port"] = 8080

        cfg["app"]["novice_mode"] = bool(cfg["app"].get("novice_mode", True))
        cfg["app"]["name"] = str(cfg["app"].get("name", "steam-friend-bot"))

        pattern = cfg["phone"].get("pattern", r"^1[3-9]\d{9}$")
        cfg["phone"]["pattern"] = str(pattern)

        return cfg

    def save_runtime_config(self, cfg: dict) -> None:
        """将配置持久化到运行时文件。"""
        with open(RUNTIME_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    def parse_config_text(self, text: str) -> dict:
        """解析 YAML 或 JSON 文本为字典。"""
        text = text.strip()
        if text.startswith("{"):
            return json.loads(text)
        return yaml.safe_load(text)

    def backup_current(self) -> str | None:
        """备份当前运行时配置，返回备份文件路径（不存在则返回 None）。"""
        if not os.path.exists(RUNTIME_PATH):
            return None
        backup_path = RUNTIME_PATH + ".bak"
        shutil.copyfile(RUNTIME_PATH, backup_path)
        return backup_path

    def restore_backup(self, backup_path: str | None) -> None:
        """从备份路径恢复配置文件。"""
        if backup_path and os.path.exists(backup_path):
            shutil.copyfile(backup_path, RUNTIME_PATH)
