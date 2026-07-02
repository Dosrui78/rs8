from abc import ABC, abstractmethod
import iv8


class BasePlugin(ABC):
    name: str = ""
    dependencies: list[str] = []

    @abstractmethod
    def apply(self, ctx: iv8.JSContext, config: dict):
        ...


_builtin_plugins = []
