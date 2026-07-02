from plugins.base import BasePlugin, _builtin_plugins
import iv8


class WasmPlugin(BasePlugin):
    name = "wasm"
    dependencies = []

    def apply(self, ctx: iv8.JSContext, config: dict):
        ctx.eval("""
            if (typeof WebAssembly === 'undefined') {
                WebAssembly = {};
            }
            WebAssembly.compile = function(buffer) {
                return Promise.resolve({});
            };
            WebAssembly.instantiate = function(mod, imports) {
                return Promise.resolve({instance: {}, module: mod});
            };
            WebAssembly.instantiateStreaming = function(resp, imports) {
                return Promise.resolve({instance: {}, module: {}});
            };
            WebAssembly.compileStreaming = function(resp) {
                return Promise.resolve({});
            };
            WebAssembly.Module = function(buffer) {};
            WebAssembly.Instance = function(mod, imports) {};
            WebAssembly.validate = function(buffer) { return true; };
        """)


_builtin_plugins.append(WasmPlugin())
