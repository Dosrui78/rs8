from plugins.base import BasePlugin, _builtin_plugins
import iv8


class WorkerPlugin(BasePlugin):
    name = "worker"
    dependencies = ["wasm"]

    def apply(self, ctx: iv8.JSContext, config: dict):
        ctx.eval("""
            var Worker = function(url) {
                this.onmessage = null;
                var self = this;
                var _postMessage = function(data) {
                    if (self.onmessage) {
                        self.onmessage({data: data});
                    }
                };
                var _close = function() {};
                var _importScripts = function() {};
                var _console = console;
            };
            Worker.prototype.postMessage = function(data) {};
            Worker.prototype.terminate = function() {};
            Worker.prototype.addEventListener = function() {};
            Worker.prototype.removeEventListener = function() {};
        """)


_builtin_plugins.append(WorkerPlugin())
