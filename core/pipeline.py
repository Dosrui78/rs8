import time
import copy
import importlib

import curl_cffi.requests as requests

from core.types import ExtractedData, BypassResult, PipelineConfig
from core.engine import JSContextFactory, PluginManager
from core.env_builder import build_environment
from detectors.auto import AutoDetector
from adapters import adapter_registry
from config import settings


_PROFILE_CACHE: dict[str, dict] = {}


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


def _extract_impersonate(ua: str) -> str:
    """从 UA 中提取 Chrome 版本号，返回 curl_cffi 的 impersonate 参数。"""
    import re
    m = re.search(r"Chrome/(\d+)", ua)
    if m:
        return f"chrome{m.group(1)}"
    return "chrome110"


class Pipeline:
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"

    def __init__(self):
        impersonate = _extract_impersonate(self.UA)
        self.session = requests.Session(impersonate=impersonate)
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

    def _fetch_rs_page(self, url: str, headers: dict, logs: list) -> tuple[int, str, ExtractedData | None]:
        self._log(logs, f"GET {url}")
        headers = headers or {}
        headers.setdefault("User-Agent", self.UA)

        resp = self.session.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        status = resp.status_code
        html = resp.text
        self._log(logs, f"  status={status} size={len(html)}")

        # 只在 RS 挑战页才抓 auto_script，避免浪费 200 页面的 cookie
        if status in {412, 202, 403}:
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
                except Exception as e:
                    self._log(logs, f"  auto_script fetch fail: {e}")
        else:
            extracted = None

        return status, html, extracted

    def _solve_one_round(self, extracted: ExtractedData, url: str, cfg, recipe, logs: list) -> str:
        """跑一轮 iv8 生成 cookie，返回 cookie 字符串。每一轮都可能需要不同的环境/适配器。"""
        profile = copy.deepcopy(_load_profile(cfg.profile))
        if recipe:
            _deep_merge(profile, recipe.profile_overrides)
        environment = build_environment(profile, url)

        adapter = adapter_registry.get(extracted.version)
        if not adapter:
            raise ValueError(f"no_adapter_for_{extracted.version}")

        ctx = self.engine_factory.create(environment)
        plugin_config = {"canvas_fp": settings.CANVAS_FINGERPRINT}
        self.engine_factory.apply_plugins(ctx, adapter.plugins, plugin_config)

        extracted.extra_hooks = recipe.before_exec_hooks if recipe else []
        cookie_str = adapter.execute(ctx, extracted, logs)
        self._log(logs, f"  cookie: {cookie_str[:80] if cookie_str else '(empty)'}...")
        return cookie_str

    def _merge_cookies_into_session(self, cookie_str: str):
        """把 JS 生成的 cookie 回注到 session。"""
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                self.session.cookies.set(k.strip(), v.strip())

    def _build_all_cookies(self, cookie_str: str) -> dict:
        """合并 session cookie + 最新 JS 生成的 cookie。"""
        all_cookies = dict(self.session.cookies)
        for item in cookie_str.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                all_cookies[k.strip()] = v.strip()
        return all_cookies

    def run(self, url: str, config: PipelineConfig | None = None) -> BypassResult:
        start = time.time()
        logs = []
        result = BypassResult(logs=logs)
        cfg = config or PipelineConfig(url=url)

        try:
            from recipes.base import recipe_matcher
            recipe = recipe_matcher.match(url)
            if recipe:
                self._log(logs, f"  匹配 Recipe: {recipe.domain}")

            headers = {**cfg.headers}
            if recipe:
                headers.update(recipe.headers_overrides)

            # 需要多轮的站点在 recipe 中声明 max_rounds
            max_rounds = getattr(recipe, "max_rounds", 1) if recipe else 1

            for round_num in range(1, max_rounds + 1):
                self._log(logs, f"=== Round {round_num} ===")

                status, html, extracted = self._fetch_rs_page(url, headers, logs)

                # 已经拿到正常页面 → 不再继续
                if status in (200, 302, 304):
                    self._log(logs, "  [✓] 已是正常页面")
                    break

                # 不是 RS 挑战码，也没有正常内容 → 失败
                if status not in {412, 202, 403}:
                    result.error = f"blocked (status={status})"
                    self._log(logs, f"  [!] 被拦截")
                    return result

                if not extracted or not extracted.ts_js:
                    result.error = "no_rs_detected"
                    self._log(logs, "  [!] 未检测到瑞数特征")
                    return result

                result.version = extracted.version
                cookie_str = self._solve_one_round(extracted, url, cfg, recipe, logs)
                if not cookie_str:
                    result.error = "cookie_empty"
                    return result

                self._merge_cookies_into_session(cookie_str)

            all_cookies = dict(self.session.cookies)
            result.cookie_dict = all_cookies
            result.cookie = "; ".join(f"{k}={v}" for k, v in all_cookies.items())
            result.success = True

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
