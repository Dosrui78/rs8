class DetectorRegistry:
    def __init__(self):
        self._detectors = {}

    def register(self, detector):
        self._detectors[detector.name] = detector

    def get(self, name: str):
        return self._detectors.get(name)

    def all(self):
        return list(self._detectors.values())


detector_registry = DetectorRegistry()
