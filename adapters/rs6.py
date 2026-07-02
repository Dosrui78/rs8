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

        # 1. set globals that hooks may reference (e.g. META_CONTENT, META_R)
        ctx.eval(f"""
            var META_CONTENT = '{meta_c}';
            var META_R = '{meta_r}';
        """)

        # 1a. inject recipe hooks if present (site-specific DOM patches)
        if data.extra_hooks:
            logs.append(f"  injecting {len(data.extra_hooks)} recipe hooks...")
            for i, hook in enumerate(data.extra_hooks):
                try:
                    ctx.eval(hook)
                    logs.append(f"  hook[{i}] injected ({len(hook)} chars)")
                except Exception as e:
                    logs.append(f"  hook[{i}] error: {e}")
        else:
            # fallback generic DOM patches
            logs.append("  injecting generic DOM patches...")
            ctx.eval(f"""
                // --- self = top = window ---
                self = top = window;

                // --- timer mocks ---
                window.setInterval = function() {{ return 0; }};
                window.setTimeout = function() {{ return 0; }};
                window.clearTimeout = function() {{}};
                window.clearInterval = function() {{}};
                window.addEventListener = function() {{}};
                window.ActiveXObject = undefined;
                window.attachEvent = function() {{}};

                // --- XHR ---
                var XMLHttpRequest = function XMLHttpRequest() {{}};
                XMLHttpRequest.prototype.open = function() {{}};
                XMLHttpRequest.prototype.send = function() {{}};
                XMLHttpRequest.prototype.setRequestHeader = function() {{}};
                XMLHttpRequest.prototype.abort = function() {{}};
                XMLHttpRequest.prototype.getResponseHeader = function() {{ return null; }};

                // --- HTML elements ---
                window.HTMLFormElement = function() {{}};
                window.HTMLAnchorElement = function() {{}};

                var _head = {{
                    removeChild: function(el) {{}},
                    appendChild: function(el) {{ return el; }},
                    insertBefore: function(el, ref) {{ return el; }}
                }};

                var _script = {{
                    getAttribute: function(k) {{ if (k === 'r') return META_R; return null; }},
                    parentElement: _head,
                    parentNode: _head,
                    src: '{data.auto_script_url}',
                    type: 'text/javascript'
                }};

                var _meta = {{
                    getAttribute: function(k) {{ if (k === 'r') return META_R; return null; }},
                    parentNode: _head,
                    content: META_CONTENT
                }};

                var _div = {{ getElementsByTagName: function(t) {{ return []; }} }};
                var _form = {{}};
                var _input = {{}};

                document.createElement = function(tag) {{
                    if (tag === 'div') return _div;
                    if (tag === 'form') return _form;
                    if (tag === 'input') return _input;
                    if (tag === 'script') return {{}};
                    return {{}};
                }};
                document.appendChild = function(el) {{}};
                document.removeChild = function(el) {{}};
                document.getElementsByTagName = function(tag) {{
                    if (tag === 'script') return [_script, _script];
                    if (tag === 'meta') return [_meta, _meta];
                    if (tag === 'head') return [_head];
                    return [];
                }};
                document.getElementById = function(id) {{
                    if (id === 'root-hammerhead-shadow-ui') return null;
                    return null;
                }};
                document.addEventListener = function() {{}};
                document.documentElement = document.body = document;
                document.querySelector = function(s) {{ return null; }};
                document.querySelectorAll = function(s) {{ return []; }};
                document.attachEvent = function() {{}};
            """)
        logs.append("  DOM patches injected")

        # 2. page.load
        logs.append("  page.load...")
        ctx.eval(f"""
            window.__iv8__.page.load({{ baseURL: '{data.auto_script_url}' }});
        """)

        # 3. ts_js
        if data.ts_js:
            logs.append(f"  executing ts_js ({len(data.ts_js)} chars)...")
            try:
                ctx.eval(data.ts_js)
                ctx.eval("window.__iv8__.eventLoop.drainMicrotasks()")
                logs.append("  ts_js ok")
            except Exception as e:
                logs.append(f"  ts_js warn: {e}")

        # 4. auto_script
        if data.auto_script_js:
            logs.append(f"  executing auto_script ({len(data.auto_script_js)} chars)...")
            try:
                ctx.eval(data.auto_script_js)
                ctx.eval("window.__iv8__.eventLoop.drainMicrotasks()")
                logs.append("  auto_script ok")
            except Exception as e:
                logs.append(f"  auto_script warn: {e}")

        # 5. wait for async cookies
        logs.append("  waiting for event loop (3s)...")
        ctx.eval("window.__iv8__.eventLoop.sleep(3000)")

        # 6. read cookie
        cookie = ctx.eval("document.cookie") or ""
        return cookie


adapter_registry.register(RS6Adapter())
