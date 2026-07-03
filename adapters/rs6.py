import iv8
from adapters.base import BaseAdapter
from adapters import adapter_registry
from core.types import ExtractedData


class RS6Adapter(BaseAdapter):
    version = "rs6"
    plugins = ["canvas", "webgl", "wasm", "worker"]

    def execute(self, ctx: iv8.JSContext, data: ExtractedData, logs: list) -> str:
        meta_c = data.meta_content
        meta_r = data.meta_r or "m"
        meta_id = data.meta_id
        ts_js = data.ts_js
        auto_script_js = data.auto_script_js
        auto_script_url = data.auto_script_url
        base_url = auto_script_url.rsplit("/", 1)[0] if auto_script_url else ""

        # 1. slice fix
        ctx.eval("""
            (function(){
                var _orig_slice = String.prototype.slice;
                String.prototype.slice = function(a, b) {
                    if (this == null) return '';
                    return _orig_slice.call(this, a, b);
                };
                var _orig_aslice = Array.prototype.slice;
                Array.prototype.slice = function(a, b) {
                    if (this == null) return [];
                    return _orig_aslice.call(this, a, b);
                };
            })();
        """)

        # 2. page.load with full HTML (let iv8's native DOM engine handle everything)
        #    Build a page equivalent to the actual RS challenge page
        meta_tag = f'<meta id="{meta_id}" content="{meta_c}" r="{meta_r}">' if meta_id else f'<meta content="{meta_c}" r="{meta_r}">'
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
{meta_tag}
<script r='{meta_r}'>{ts_js}</script>
<script src="{auto_script_url}"></script>
</head>
<body></body>
</html>"""

        resources = {}
        if auto_script_js:
            resources[auto_script_url] = auto_script_js

        logs.append("  page.load with native DOM...")
        try:
            ctx.eval(f"""
                window.__iv8__.page.load({{
                    baseURL: '{auto_script_url}',
                    html: {repr(html)},
                    resources: {repr(resources)}
                }});
            """)
            logs.append("  page.load ok")
        except Exception as e:
            logs.append(f"  page.load warn: {e}")

        # 3. wait for cookie generation
        logs.append("  waiting for event loop (3s)...")
        ctx.eval("window.__iv8__.eventLoop.sleep(3000)")

        # 4. read cookie
        cookie = ctx.eval("document.cookie") or ""
        return cookie


adapter_registry.register(RS6Adapter())
