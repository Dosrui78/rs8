from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Recipe:
    """站点配方：覆盖自动检测/适配的逻辑"""
    domain: str                          # 匹配域名，如 "www.ouyeel.com"
    version_hint: str = ""               # 强制指定版本
    max_rounds: int = 1                  # 需几轮 RS 解密（cebwm 要 2 轮）
    before_exec_hooks: list[str] = field(default_factory=list)   # ts_js 执行前注入的 JS
    after_exec_hooks: list[str] = field(default_factory=list)    # ts_js 执行后注入的 JS
    profile_overrides: dict = field(default_factory=dict)        # 覆盖指纹配置
    headers_overrides: dict = field(default_factory=dict)        # 覆盖请求头


class RecipeMatcher:
    """URL 匹配 + 返回对应 recipe"""
    def __init__(self):
        self._recipes: dict[str, Recipe] = {}
        self._wildcards: list[tuple[str, Recipe]] = []

    def register(self, recipe: Recipe):
        if recipe.domain.startswith("*."):
            self._wildcards.append((recipe.domain[1:], recipe))
        else:
            self._recipes[recipe.domain] = recipe

    def match(self, url: str) -> Optional[Recipe]:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        # exact match
        if host in self._recipes:
            return self._recipes[host]
        # wildcard
        for suffix, recipe in self._wildcards:
            if host.endswith(suffix):
                return recipe
        return None


recipe_matcher = RecipeMatcher()
