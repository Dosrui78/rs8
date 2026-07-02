import time
import copy
import importlib
import requests

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
        import recipes.ouyeel

    def _log(self, logs, msg):
        print(f"  {msg}")
        logs.append(msg)

    def _fetch_rs_page(self, url: str, headers: dict, logs: list) -> tuple[str, ExtractedData]:
        self._log(logs, f"GET {url}")
        headers = headers or {}
        headers.setdefault("User-Agent", self.UA)
        resp = self.session.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
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
            result.cookie = cookie_str
            for item in cookie_str.split(";"):
                item = item.strip()
                if "=" in item:
                    k, v = item.split("=", 1)
                    result.cookie_dict[k.strip()] = v.strip()

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
