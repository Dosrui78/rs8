from plugins.base import BasePlugin, _builtin_plugins
import iv8


class WebGLPlugin(BasePlugin):
    name = "webgl"
    dependencies = []

    def apply(self, ctx: iv8.JSContext, config: dict):
        ctx.eval("""
            HTMLCanvasElement.prototype.getContext = (function(orig) {
                return function(type, attrs) {
                    if (type === 'webgl' || type === 'experimental-webgl') {
                        return {
                            drawingBufferWidth: 1920,
                            drawingBufferHeight: 1080,
                            getParameter: function(p) { return null; },
                            getExtension: function(name) { return null; },
                            getSupportedExtensions: function() { return []; },
                            getShaderPrecisionFormat: function() { return {rangeMin: 127, rangeMax: 127, precision: 23}; },
                            createShader: function() { return {}; },
                            shaderSource: function() {},
                            compileShader: function() {},
                            getShaderParameter: function() { return true; },
                            createProgram: function() { return {}; },
                            attachShader: function() {},
                            linkProgram: function() {},
                            getProgramParameter: function() { return true; },
                            useProgram: function() {},
                            getAttribLocation: function() { return 0; },
                            getUniformLocation: function() { return {}; },
                            uniformMatrix4fv: function() {},
                            uniform3f: function() {},
                            uniform1i: function() {},
                            enable: function() {},
                            disable: function() {},
                            blendFunc: function() {},
                            clearColor: function() {},
                            clear: function() {},
                            viewport: function() {},
                            bindBuffer: function() {},
                            bufferData: function() {},
                            enableVertexAttribArray: function() {},
                            vertexAttribPointer: function() {},
                            drawArrays: function() {},
                            getBufferParameter: function() { return {}; },
                            getError: function() { return 0; },
                            readPixels: function(x, y, w, h, format, type, pixels) {
                                if (pixels && pixels.__iv8_buffer) {
                                    pixels.__iv8_buffer.fill(0);
                                }
                            },
                            isContextLost: function() { return false; },
                            getContextAttributes: function() { return {alpha: true, antialias: true}; },
                        };
                    }
                    return orig.call(this, type, attrs);
                };
            })(HTMLCanvasElement.prototype.getContext);
        """)


_builtin_plugins.append(WebGLPlugin())
