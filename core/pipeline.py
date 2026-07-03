import time
import copy
import importlib
import re
import subprocess

import requests

from core.types import ExtractedData, BypassResult, PipelineConfig
from core.engine import JSContextFactory, PluginManager
from core.env_builder import build_environment
from detectors.auto import AutoDetector
from adapters import adapter_registry
from config import settings


_PROFILE_CACHE: dict[str, dict] = {}


def _legacy_ssl_fetch(url: str, headers: dict, timeout: int) -> requests.Response:
    """对于 OpenSSL 3.x 拒绝连接的旧式服务器，退到 curl 抓取。"""
    cmd = ["curl", "-s", "-D", "-", url, "--max-time", str(timeout)]
    for k, v in headers.items():
        cmd += ["-H", f"{k}: {v}"]

    proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
    output = proc.stdout.decode("utf-8", errors="replace")

    # curl -D - 输出格式：HTTP 头 + 空行 + body
    header_end = output.find("\r\n\r\n")
    if header_end < 0:
        header_end = output.find("\n\n")
    if header_end < 0:
        raise Exception("curl returned no valid HTTP response")

    header_text = output[:header_end]
    body = output[header_end:].strip()

    # 解析 status line
    status_line = header_text.splitlines()[0] if header_text.strip() else "HTTP/1.1 000"
    parts = status_line.split()
    status_code = int(parts[1]) if len(parts) >= 2 else 0

    # 构造一个类 Response 对象
    resp = requests.Response()
    resp.status_code = status_code
    resp._content = body.encode("utf-8")

    # 解析 Set-Cookie 到 resp.cookies（只取第一个 key=value，后面是属性）
    for line in header_text.splitlines():
        if line.lower().startswith("set-cookie:"):
            cookie_str = line[len("set-cookie:"):].strip()
            parts = cookie_str.split(";")
            for item in parts:
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    k = k.strip()
                    # 跳过 cookie 属性字段
                    if k.lower() in ("path", "expires", "domain", "max-age", "httponly", "secure", "samesite"):
                        continue
                    resp.cookies.set(k, v.strip())
                    break  # 只取第一个 key=value

    return resp


def _is_legacy_ssl_error(exc: Exception) -> bool:
    """判断是否是 OpenSSL 旧式重协商被禁的错。"""
    msg = str(exc)
    return "UNSAFE_LEGACY_RENEGOTIATION_DISABLED" in msg or "unsafe legacy renegotiation" in msg.lower()


def _load_profile(name: str) -> dict:
    if name in _PROFILE_CACHE:
        return _PROFILE_CACHE[name]
    mod = importlib.import_module(f"profiles.{name}")
    for key in dir(mod):
        if key.startswith(("CHROME_", "FIREFOX_", "EDGE_")):
            profile = getattr(mod, key)
            _PROFILE_CACHE[name] = profile
            return profile
    msg = f"profile '{name}' not found (no CHROME_/FIREFOX_/EDGE_* constant)"
    raise ValueError(msg)


class Pipeline:
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"

    def __init__(self):
        self.session = requests.Session()
        self.detector = AutoDetector()
        self.plugin_manager = PluginManager()
        self.engine_factory = JSContextFactory(self.plugin_manager)
        self._register_defaults()

    def _register_defaults(self):
        import plugins.canvas
        import plugins.webgl
        import plugins.wasm
        import plugins.worker
        from plugins.base import _builtin_plugins
        for p in _builtin_plugins:
            self.plugin_manager.register(p)
        # recipes are auto-discovered via recipes/__init__.py

    def _log(self, logs, msg):
        print(f"  {msg}")
        logs.append(msg)

    def _fetch_rs_page(self, url: str, headers: dict, logs: list) -> tuple[str, ExtractedData]:
        self._log(logs, f"GET {url}")
        headers = headers or {}
        headers.setdefault("User-Agent", self.UA)

        try:
            resp = self.session.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        except requests.exceptions.SSLError as e:
            if _is_legacy_ssl_error(e):
                self._log(logs, "  SSL legacy renegotiation blocked, retrying with curl...")
                try:
                    resp = _legacy_ssl_fetch(url, headers, settings.REQUEST_TIMEOUT)
                    # 把 curl 拿到的 cookie 回注到 session
                    self.session.cookies.update(resp.cookies)
                except Exception as e2:
                    raise Exception(f"curl fallback also failed: {e2}") from e
            else:
                raise

        self._log(logs, f"  status={resp.status_code} size={len(resp.text)}")

        html = resp.text
        extracted = self.detector.detect(html)

        if extracted and extracted.auto_script_url:
            if not extracted.auto_script_url.startswith("http"):
                from urllib.parse import urljoin
                extracted.auto_script_url = urljoin(url, extracted.auto_script_url)
            self._log(logs, f"  fetch auto_script: {extracted.auto_script_url}")
            try:
                js_resp = self.session.get(
                    extracted.auto_script_url,
                    headers={"User-Agent": self.UA},
                    timeout=settings.REQUEST_TIMEOUT,
                )
                extracted.auto_script_js = js_resp.text
                self._log(logs, f"  auto_script: {len(extracted.auto_script_js)} chars")
            except requests.exceptions.SSLError as e:
                if _is_legacy_ssl_error(e):
                    self._log(logs, "  auto_script SSL legacy, retrying with curl...")
                    try:
                        js_resp = _legacy_ssl_fetch(
                            extracted.auto_script_url,
                            {"User-Agent": self.UA},
                            settings.REQUEST_TIMEOUT,
                        )
                        extracted.auto_script_js = js_resp.text
                        self._log(logs, f"  auto_script: {len(extracted.auto_script_js)} chars")
                    except Exception as e2:
                        self._log(logs, f"  auto_script fetch fail: {e2}")
                else:
                    self._log(logs, f"  auto_script fetch fail: {e}")
            except Exception as e:
                self._log(logs, f"  auto_script fetch fail: {e}")

        return html, extracted

    def run(self, url: str, config: PipelineConfig | None = None) -> BypassResult:
        start = time.time()
        logs = []
        result = BypassResult(logs=logs)

        cfg = config or PipelineConfig(url=url)

        try:
            # 0. resolve recipe
            from recipes.base import recipe_matcher
            recipe = recipe_matcher.match(url)
            if recipe:
                self._log(logs, f"  匹配 Recipe: {recipe.domain}")

            # 1. fetch HTML
            self._log(logs, "=== Phase 1: Fetch ===")
            headers = {**cfg.headers}
            if recipe:
                headers.update(recipe.headers_overrides)
            html, extracted = self._fetch_rs_page(url, headers, logs)

            if not extracted or not extracted.ts_js:
                result.error = "no_rs_detected"
                self._log(logs, "  [!] 未检测到瑞数特征")
                return result

            result.version = extracted.version
            self._log(logs, f"  检测版本: {extracted.version}")

            # 2. build environment + recipe overrides
            self._log(logs, "=== Phase 2: Build env ===")
            profile = copy.deepcopy(_load_profile(cfg.profile))
            if recipe:
                _deep_merge(profile, recipe.profile_overrides)
            environment = build_environment(profile, url)
            self._log(logs, f"  env built (profile={cfg.profile})")

            # 3. get adapter
            adapter = adapter_registry.get(extracted.version)
            if not adapter:
                result.error = f"no_adapter_for_{extracted.version}"
                self._log(logs, f"  [!] 无适配器: {extracted.version}")
                return result

            # 4. create iv8 context and apply plugins
            self._log(logs, "=== Phase 3: iv8 execute ===")
            ctx = self.engine_factory.create(environment)
            plugin_config = {"canvas_fp": settings.CANVAS_FINGERPRINT}
            self.engine_factory.apply_plugins(ctx, adapter.plugins, plugin_config)
            self._log(logs, "  plugins applied")

            # 5. execute adapter with recipe
            extracted.extra_hooks = recipe.before_exec_hooks if recipe else []
            cookie_str = adapter.execute(ctx, extracted, logs)
            self._log(logs, f"  cookie: {cookie_str[:80] if cookie_str else '(empty)'}...")

            if not cookie_str:
                result.error = "cookie_empty"
                return result

            result.success = True

            # merge session cookies (server-set e.g. 6HZbKHDjIEcgS) with
            # generated cookies (client-side e.g. 6HZbKHDjIEcgT)
            session_cookies = dict(self.session.cookies)
            all_cookies = {}
            all_cookies.update(session_cookies)
            for item in cookie_str.split(";"):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    all_cookies[k.strip()] = v.strip()
            result.cookie_dict = all_cookies
            result.cookie = "; ".join(f"{k}={v}" for k, v in all_cookies.items())

        except Exception as e:
            result.error = str(e)
            self._log(logs, f"  [!] 错误: {e}")

        result.elapsed = round(time.time() - start, 2)
        self._log(logs, f"=== Done ({result.elapsed}s) ===")
        return result


def _deep_merge(base: dict, overrides: dict):
    """递归合并 dict，overrides 覆盖 base"""
    for k, v in overrides.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = copy.deepcopy(v)
