import re
from detectors.base import BaseDetector
from core.types import ExtractedData


class RS6Detector(BaseDetector):
    name = "rs6"

    def detect(self, html: str) -> ExtractedData | None:
        data = ExtractedData(version="rs6")

        # meta content + r (two possible orderings)
        mc = re.search(r'<meta\s+content="([^"]*)"\s+r="([^"]*)"', html)
        if mc:
            data.meta_content = mc.group(1)
            data.meta_r = mc.group(2)
            data.features["has_meta"] = True
        else:
            mc = re.search(r'<meta\s+r="([^"]*)"\s+content="([^"]*)"', html)
            if mc:
                data.meta_r = mc.group(1)
                data.meta_content = mc.group(2)
                data.features["has_meta"] = True

        # ts_js: $_ts.tsd / $_ts.cd / $_ts.hp
        ts = re.search(r'<script[^>]*>\s*(\$_ts.*?)</script>', html, re.DOTALL)
        if ts:
            data.ts_js = ts.group(1)
            data.features["has_ts"] = True

        # external auto script
        ext = re.search(r'<script\s+[^>]*src="([^"]+)"', html)
        if ext:
            data.auto_script_url = ext.group(1)
            data.features["has_external"] = True

        if data.features.get("has_ts") or data.features.get("has_external"):
            return data
        return None
