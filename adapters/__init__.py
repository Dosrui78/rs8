class AdapterRegistry:
    def __init__(self):
        self._adapters = {}

    def register(self, adapter):
        self._adapters[adapter.version] = adapter

    def get(self, version: str):
        return self._adapters.get(version)


adapter_registry = AdapterRegistry()

# Import adapters after registry is created (they register on import)
import os, importlib
_dir = os.path.dirname(__file__)
for f in os.listdir(_dir):
    if f.endswith(".py") and f not in ("__init__.py", "base.py"):
        importlib.import_module(f"adapters.{f[:-3]}")
