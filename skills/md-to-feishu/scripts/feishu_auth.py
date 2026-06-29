"""Feishu OAuth (user) and tenant token helpers."""

from __future__ import annotations

import json
import os
import secrets as secrets_module
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import requests

DEFAULT_DOMAIN = "open.feishu.cn"
SECRETS_PATH = Path.home() / ".jeemoo" / "secrets.env"
TOKEN_STORE_PATH = Path.home() / ".jeemoo" / "feishu_user_token.json"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/callback"
DEFAULT_OAUTH_PORT = 8765
OAUTH_SCOPES = "docs:document:import offline_access"
TOKEN_EXPIRY_BUFFER_SEC = 120


def load_secrets(path: Path = SECRETS_PATH) -> dict[str, str]:
    secrets_map: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            secrets_map[key.strip()] = value.strip().strip('"').strip("'")
    for key in (
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_FOLDER_TOKEN",
        "FEISHU_DOMAIN",
        "FEISHU_REDIRECT_URI",
    ):
        env_val = os.environ.get(key)
        if env_val:
            secrets_map[key] = env_val
    return secrets_map


def api_base(domain: str) -> str:
    return f"https://{domain}/open-apis"


def feishu_error(payload: dict[str, Any]) -> str:
    return f"code={payload.get('code')} msg={payload.get('msg', payload.get('error_description', ''))}"


def load_token_store(path: Path = TOKEN_STORE_PATH) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def save_token_store(data: dict[str, Any], path: Path = TOKEN_STORE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    path.chmod(0o600)


def build_authorize_url(
    app_id: str,
    redirect_uri: str,
    state: str,
    scopes: str = OAUTH_SCOPES,
) -> str:
    query = urlencode(
        {
            "client_id": app_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "state": state,
            "prompt": "consent",
        }
    )
    return f"https://accounts.feishu.cn/open-apis/authen/v1/authorize?{query}"


def exchange_code_for_token(
    domain: str,
    app_id: str,
    app_secret: str,
    code: str,
    redirect_uri: str,
) -> dict[str, Any]:
    url = f"{api_base(domain)}/authen/v2/oauth/token"
    resp = requests.post(
        url,
        json={
            "grant_type": "authorization_code",
            "client_id": app_id,
            "client_secret": app_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"换取 user_access_token 失败: {feishu_error(data)}")
    return data


def refresh_user_token(
    domain: str,
    app_id: str,
    app_secret: str,
    refresh_token: str,
) -> dict[str, Any]:
    url = f"{api_base(domain)}/authen/v2/oauth/token"
    resp = requests.post(
        url,
        json={
            "grant_type": "refresh_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"刷新 user_access_token 失败: {feishu_error(data)}")
    return data


def token_store_from_oauth_response(data: dict[str, Any], app_id: str) -> dict[str, Any]:
    now = int(time.time())
    store: dict[str, Any] = {
        "app_id": app_id,
        "access_token": data["access_token"],
        "expires_at": now + int(data.get("expires_in", 7200)),
        "scope": data.get("scope", ""),
    }
    if data.get("refresh_token"):
        store["refresh_token"] = data["refresh_token"]
        store["refresh_expires_at"] = now + int(data.get("refresh_token_expires_in", 604800))
    return store


def get_tenant_access_token(domain: str, app_id: str, app_secret: str) -> str:
    url = f"{api_base(domain)}/auth/v3/tenant_access_token/internal"
    resp = requests.post(
        url,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 tenant_access_token 失败: {feishu_error(data)}")
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError("tenant_access_token 为空")
    return token


def get_user_access_token(secrets: dict[str, str]) -> str:
    app_id = secrets.get("FEISHU_APP_ID")
    app_secret = secrets.get("FEISHU_APP_SECRET")
    domain = secrets.get("FEISHU_DOMAIN") or DEFAULT_DOMAIN
    if not app_id or not app_secret:
        raise RuntimeError(
            "缺少飞书应用凭证。请在 ~/.jeemoo/secrets.env 配置 FEISHU_APP_ID 与 FEISHU_APP_SECRET。"
        )

    store = load_token_store()
    now = int(time.time())

    if store and store.get("app_id") == app_id:
        expires_at = int(store.get("expires_at", 0))
        if store.get("access_token") and expires_at - TOKEN_EXPIRY_BUFFER_SEC > now:
            return store["access_token"]

        refresh_token = store.get("refresh_token")
        refresh_expires_at = int(store.get("refresh_expires_at", 0))
        if refresh_token and refresh_expires_at > now:
            refreshed = refresh_user_token(domain, app_id, app_secret, refresh_token)
            new_store = token_store_from_oauth_response(refreshed, app_id)
            save_token_store(new_store)
            return new_store["access_token"]

    raise RuntimeError(
        "尚未完成用户授权或 token 已过期。请先运行：\n"
        "  python ~/.cursor/skills/md-to-feishu/scripts/md2feishu.py login"
    )


def oauth_login(secrets: dict[str, str]) -> dict[str, Any]:
    app_id = secrets.get("FEISHU_APP_ID")
    app_secret = secrets.get("FEISHU_APP_SECRET")
    domain = secrets.get("FEISHU_DOMAIN") or DEFAULT_DOMAIN
    redirect_uri = secrets.get("FEISHU_REDIRECT_URI") or DEFAULT_REDIRECT_URI

    if not app_id or not app_secret:
        raise RuntimeError(
            "缺少飞书应用凭证。请在 ~/.jeemoo/secrets.env 配置 FEISHU_APP_ID 与 FEISHU_APP_SECRET。"
        )

    state = secrets_module.token_urlsafe(24)
    auth_url = build_authorize_url(app_id, redirect_uri, state)
    result: dict[str, str | None] = {"code": None, "error": None}

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != urlparse(redirect_uri).path:
                self.send_error(404)
                return

            params = parse_qs(parsed.query)
            if params.get("state", [""])[0] != state:
                result["error"] = "state 校验失败"
                self._respond("授权失败：state 不匹配，请重试。", success=False)
                return

            if "error" in params:
                result["error"] = params["error"][0]
                self._respond("你已取消授权。", success=False)
                return

            code = params.get("code", [""])[0]
            if not code:
                result["error"] = "missing code"
                self._respond("授权失败：未收到 code。", success=False)
                return

            result["code"] = code
            self._respond("授权成功，可以关闭此页面并返回终端。", success=True)

        def _respond(self, message: str, *, success: bool) -> None:
            color = "#16a34a" if success else "#dc2626"
            body = f"""<!doctype html><html><head><meta charset="utf-8"><title>飞书授权</title></head>
<body style="font-family:sans-serif;padding:40px;text-align:center">
<h2 style="color:{color}">{message}</h2>
<p>返回 Cursor / 终端继续操作。</p>
</body></html>"""
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    parsed_redirect = urlparse(redirect_uri)
    port = parsed_redirect.port or DEFAULT_OAUTH_PORT
    server = HTTPServer(("127.0.0.1", port), CallbackHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    print(f"正在打开浏览器，请用你的飞书账号完成授权…")
    print(f"若未自动打开，请访问：\n{auth_url}\n")
    webbrowser.open(auth_url)

    thread.join(timeout=300)
    server.server_close()

    if not result["code"]:
        err = result["error"] or "超时"
        raise RuntimeError(f"用户授权未完成: {err}")

    token_data = exchange_code_for_token(domain, app_id, app_secret, result["code"], redirect_uri)
    store = token_store_from_oauth_response(token_data, app_id)
    save_token_store(store)
    return store


def resolve_access_token(secrets: dict[str, str], mode: str) -> str:
    domain = secrets.get("FEISHU_DOMAIN") or DEFAULT_DOMAIN
    app_id = secrets.get("FEISHU_APP_ID")
    app_secret = secrets.get("FEISHU_APP_SECRET")

    if mode == "user":
        return get_user_access_token(secrets)
    if mode == "app":
        if not app_id or not app_secret:
            raise RuntimeError("应用模式需要 FEISHU_APP_ID 与 FEISHU_APP_SECRET")
        return get_tenant_access_token(domain, app_id, app_secret)
    raise ValueError(f"未知模式: {mode}")
