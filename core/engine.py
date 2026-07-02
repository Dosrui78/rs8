import iv8
from core.types import BypassResult


class JSContextFactory:
    def __init__(self, plugin_manager=None):
        self._plugin_manager = plugin_manager

    def create(self, environment: dict, time_mode="logical") -> iv8.JSContext:
        ctx = iv8.JSContext(
            environment=environment,
            time_mode=time_mode,
        )
        return ctx

    def apply_plugins(self, ctx: iv8.JSContext, plugin_names: list[str], config: dict):
        if not self._plugin_manager:
            return
        self._plugin_manager.apply_all(ctx, plugin_names, config)


class PluginManager:
    def __init__(self):
        self._plugins = {}

    def register(self, plugin):
        self._plugins[plugin.name] = plugin

    def get(self, name: str):
        return self._plugins.get(name)

    def resolve(self, names: list[str]) -> list:
        ordered = []
        visited = set()
        def dfs(n):
            if n in visited:
                return
            visited.add(n)
            p = self._plugins.get(n)
            if p:
                for dep in p.dependencies:
                    dfs(dep)
                ordered.append(p)
        for n in names:
            dfs(n)
        return ordered

    def apply_all(self, ctx: iv8.JSContext, names: list[str], config: dict):
        plugins = self.resolve(names)
        for p in plugins:
            p.apply(ctx, config)
