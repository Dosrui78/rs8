# Auto-discover and import all recipe modules
import os
import importlib

_dir = os.path.dirname(__file__)
for f in os.listdir(_dir):
    if f.endswith(".py") and f not in ("__init__.py", "base.py"):
        modname = f"recipes.{f[:-3]}"
        importlib.import_module(modname)
