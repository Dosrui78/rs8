import re
from detectors.base import BaseDetector
from core.types import ExtractedData


class RS6Detector(BaseDetector):
    name = "rs6"

    def detect(self, html: str) -> ExtractedData | None:
        data = ExtractedData(version="rs6")

        # 取同时带 content 和 r 属性的 <meta>（兼容双/单引号混写、任意属性顺序）
        meta_content, meta_r, meta_id = _extract_meta_content_r(html)
        if meta_content:
            data.meta_content = meta_content
            data.features["has_meta"] = True
        if meta_r:
            data.meta_r = meta_r
        if meta_id:
            data.meta_id = meta_id

        # ts_js: $_ts.nsd / $_ts.cd / $_ts.hp
        ts = re.search(r"<script[^>]*>\s*(\$_ts.*?)</script>", html, re.DOTALL)
        if ts:
            data.ts_js = ts.group(1)
            data.features["has_ts"] = True

        # external auto script
        ext = re.search(r'<script\s+[^>]*src="([^"]+)"', html)
        if ext:
            data.auto_script_url = ext.group(1)
            data.features["has_external"] = True

        # trailing inline call: 紧跟 auto_script 的 _$_S() / _$$W() 等
        tail = re.search(
            r"""<script[^>]*r=["']m["'][^>]*>\s*([_$][\w$]+)\s*\(\s*\)\s*;\s*</script>""",
            html
        )
        if tail:
            data.features["inline_call"] = tail.group(1)

        if data.features.get("has_ts") or data.features.get("has_external"):
            return data
        return None


def _extract_meta_content_r(html: str) -> tuple[str, str, str]:
    """从同一 <meta> 标签中提取 content、r、id 属性值。"""
    for m in re.finditer(r"<meta\b[^>]*>", html):
        tag = m.group(0)
        c = re.search(r"""content=(["'])(.*?)\1""", tag)
        r = re.search(r"""r=(["'])(.*?)\1""", tag)
        if c and r:
            mid = re.search(r"""id=(["'])(.*?)\1""", tag)
            meta_id = mid.group(2) if mid else ""
            return c.group(2), r.group(2), meta_id
    return "", "", ""
