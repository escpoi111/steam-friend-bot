"""pytest 测试：Flask Web UI 关键端点。"""

import json
import io
import pytest

from app import app as flask_app


@pytest.fixture()
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# /healthz
# ---------------------------------------------------------------------------

def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert "service" in data


# ---------------------------------------------------------------------------
# /api/run — 手机号校验
# ---------------------------------------------------------------------------

def test_run_phone_valid(client):
    resp = client.post(
        "/api/run",
        data=json.dumps({"phone": "13800138000"}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["phone"] == "13800138000"


def test_run_phone_invalid_short(client):
    resp = client.post(
        "/api/run",
        data=json.dumps({"phone": "123"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False


def test_run_phone_invalid_prefix(client):
    """以 1 开头但第二位不在 3-9 范围内。"""
    resp = client.post(
        "/api/run",
        data=json.dumps({"phone": "12345678901"}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False


def test_run_phone_missing(client):
    resp = client.post(
        "/api/run",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# /api/config
# ---------------------------------------------------------------------------

def test_get_config(client):
    resp = client.get("/api/config")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "server" in data["data"]


# ---------------------------------------------------------------------------
# /api/config/import — 文件上传
# ---------------------------------------------------------------------------

def test_import_config_yaml_file(client):
    yaml_content = b"server:\n  port: 9090\napp:\n  novice_mode: true\n  name: test\nphone:\n  pattern: '^1[3-9]\\\\d{9}$'\n"
    data = {"file": (io.BytesIO(yaml_content), "config.yaml")}
    resp = client.post(
        "/api/config/import",
        data=data,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True


def test_import_config_json_body(client):
    payload = {
        "config": {
            "server": {"port": 8081},
            "app": {"novice_mode": False, "name": "bot"},
            "phone": {"pattern": r"^1[3-9]\d{9}$"},
        }
    }
    resp = client.post(
        "/api/config/import",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True


def test_import_config_invalid_no_config_key(client):
    """JSON body 缺少 config 字段，应返回 400 并回滚。"""
    resp = client.post(
        "/api/config/import",
        data=json.dumps({"wrong_key": {}}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["success"] is False
