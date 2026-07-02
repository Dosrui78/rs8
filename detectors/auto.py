from detectors.rs6 import RS6Detector
from core.types import ExtractedData


class AutoDetector:
    def __init__(self):
        self._detectors = [RS6Detector()]

    def detect(self, html: str) -> ExtractedData | None:
        for d in self._detectors:
            result = d.detect(html)
            if result:
                return result
        return None
