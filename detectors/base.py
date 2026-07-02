from abc import ABC, abstractmethod
from core.types import ExtractedData


class BaseDetector(ABC):
    name: str = ""

    @abstractmethod
    def detect(self, html: str) -> ExtractedData | None:
        ...
