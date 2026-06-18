"""Flask Web UI — Steam Friend Bot 傻瓜式配置入口。"""

import re
import socket

from flask import Flask, jsonify, request, send_from_directory

from services.config_service import ConfigService

app = Flask(__name__, static_folder="web", static_url_path="/")

_cfg_service = ConfigService()
_cfg = _cfg_service.bootstrap()

PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------

def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return send_from_directory("web", "index.html")


@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "service": "steam-friend-bot"}), 200


@app.post("/api/run")
def run_phone():
    """校验手机号并返回处理结果。"""
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()

    if not PHONE_PATTERN.match(phone):
        return (
            jsonify(
                {
                    "success": False,
                    "message": "手机号格式不正确，请输入 11 位中国大陆手机号",
                    "data": None,
                }
            ),
            400,
        )

    result = {
        "phone": phone,
        "normalized": phone,
        "status": "processed",
    }
    return jsonify({"success": True, "message": "处理成功", "data": result})


@app.post("/api/config/import")
def import_config():
    """支持文件上传（multipart）或 JSON 体两种方式导入配置。"""
    global _cfg
    backup_path = _cfg_service.backup_current()

    try:
        if "file" in request.files:
            f = request.files["file"]
            if not f.filename:
                raise ValueError("未选择配置文件")
            content = f.read().decode("utf-8")
            new_cfg = _cfg_service.parse_config_text(content)
        else:
            body = request.get_json(silent=True) or {}
            new_cfg = body.get("config")
            if not isinstance(new_cfg, dict):
                raise ValueError("JSON 模式下必须提供 config 对象")

        merged = _cfg_service.validate_and_fill(new_cfg)
        _cfg_service.save_runtime_config(merged)
        _cfg = merged
        return jsonify({"success": True, "message": "配置导入成功", "data": merged})

    except Exception as exc:  # noqa: BLE001
        _cfg_service.restore_backup(backup_path)
        return (
            jsonify({"success": False, "message": f"导入失败，已回滚：{exc}"}),
            400,
        )


@app.get("/api/config")
def get_config():
    return jsonify({"success": True, "data": _cfg})


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(_cfg.get("server", {}).get("port", 8080))
    while not _port_available(port):
        port += 1
    print(f"Server running at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
