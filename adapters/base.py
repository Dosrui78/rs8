from abc import ABC, abstractmethod
import iv8
from core.types import ExtractedData


class BaseAdapter(ABC):
    version: str = ""
    plugins: list[str] = []

    @abstractmethod
    def execute(self, ctx: iv8.JSContext, data: ExtractedData, logs: list) -> str:
        ...
