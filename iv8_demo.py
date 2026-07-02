"""
iv8 Demo - Python 原生 V8 + 浏览器环境运行时 测试用例
"""
import iv8
import threading
import time

def demo_basic_eval():
    """1. 基础 JS 执行与类型转换"""
    print("=" * 60)
    print("1. 基础 JS 执行与类型转换")
    print("=" * 60)
    with iv8.JSContext() as ctx:
        print(f"  int:    {ctx.eval('42')}")
        print(f"  str:    {ctx.eval(chr(39)+'hello'+chr(39))}")
        print(f"  list:   {ctx.eval('[1, 2, 3]')}")
        print(f"  bool:   {ctx.eval('true')}")
        print(f"  null:   {ctx.eval('null')}")
        print(f"  undef:  {ctx.eval('undefined')}")
        # ES6+ 解构
        ctx.eval("""
            const { name, scores } = { name: 'Alice', scores: [90, 85, 92] };
            var avg = scores.reduce((a, b) => a + b, 0) / scores.length;
        """)
        print(f"  ES6 avg: {ctx.eval('avg')}")
        # to_py=True 递归转换
        data = ctx.eval("({name: 'test', items: [1,2,3]})", to_py=True)
        print(f"  to_py:  {data}")

def demo_browser_env():
    """2. 浏览器环境与指纹"""
    print("\n" + "=" * 60)
    print("2. 浏览器环境与指纹配置")
    print("=" * 60)
    with iv8.JSContext(environment={
        "navigator": {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "platform": "Win32",
            "language": "zh-CN",
            "languages": ["zh-CN", "en-US"],
            "hardwareConcurrency": 8,
            "deviceMemory": 8,
        },
        "screen": {
            "width": 1920, "height": 1080, "colorDepth": 24,
        },
        "location": {
            "href": "https://example.com/page",
        },
    }) as ctx:
        print(f"  userAgent: {ctx.eval('navigator.userAgent')}")
        print(f"  platform:  {ctx.eval('navigator.platform')}")
        print(f"  language:  {ctx.eval('navigator.language')}")
        print(f"  hwCore:    {ctx.eval('navigator.hardwareConcurrency')}")
        print(f"  devMem:    {ctx.eval('navigator.deviceMemory')}")
        print(f"  scrW:      {ctx.eval('screen.width')}")
        print(f"  scrH:      {ctx.eval('screen.height')}")
        print(f"  webdriver: {ctx.eval('navigator.webdriver')}")
        print(f"  URL:       {ctx.eval('document.URL')}")

def demo_dom():
    """3. DOM 操作与 page.load"""
    print("\n" + "=" * 60)
    print("3. DOM 操作与 page.load")
    print("=" * 60)
    with iv8.JSContext() as ctx:
        # page.load 流式加载
        ctx.eval("""
            window.__iv8__.page.load({
                baseURL: 'https://example.com',
                html: `<html>
                    <head><title>Test Page</title></head>
                    <body>
                        <div id="app">
                            <h1>Hello iv8</h1>
                            <ul>
                                <li class="item">Item 1</li>
                                <li class="item">Item 2</li>
                                <li class="item">Item 3</li>
                            </ul>
                            <button id="btn">Click Me</button>
                        </div>
                    </body>
                </html>`,
                resources: {
                    'https://example.com/app.js': { body: 'window.APP_LOADED = true;' }
                }
            });
        """)
        print(f"  title:    {ctx.eval('document.title')}")
        print(f"  h1:       {ctx.eval('document.querySelector(\"h1\").textContent')}")
        print(f"  items:    {ctx.eval('document.querySelectorAll(\".item\").length')}")
        print(f"  btn:      {ctx.eval('document.getElementById(\"btn\").textContent')}")
        print(f"  URL:      {ctx.eval('document.URL')}")
        print(f"  appJS:    {ctx.eval('window.APP_LOADED')}")

def demo_event_loop():
    """4. 事件循环与定时器"""
    print("\n" + "=" * 60)
    print("4. 事件循环与定时器")
    print("=" * 60)
    with iv8.JSContext(time_mode="logical") as ctx:
        ctx.eval("""
            var log = [];
            setTimeout(() => log.push('macro-100'), 100);
            setTimeout(() => log.push('macro-200'), 200);
            setTimeout(() => log.push('macro-50'), 50);
            Promise.resolve().then(() => log.push('micro-1'));
            Promise.resolve().then(() => log.push('micro-2'));
            queueMicrotask(() => log.push('micro-3'));
        """)
        ctx.eval("window.__iv8__.eventLoop.advance(250)")
        result = ctx.eval("log", to_py=True)
        print(f"  执行顺序: {result}")
        print(f"  说明: micro 优先于 macro, macro 按时间排序")

def demo_network():
    """5. 网络请求拦截"""
    print("\n" + "=" * 60)
    print("5. 网络请求拦截 (离线资源)")
    print("=" * 60)
    with iv8.JSContext() as ctx:
        ctx.eval("""
            window.__iv8__.page.load({
                baseURL: 'https://example.com',
                html: '<html><body></body></html>',
                resources: {
                    'https://api.example.com/data': {
                        body: JSON.stringify({status: 'ok', items: [1,2,3]}),
                        status: 200,
                        headers: [['content-type', 'application/json']]
                    }
                }
            });
        """)
        # XHR 同步请求
        ctx.eval("""
            var xhr = new XMLHttpRequest();
            xhr.open('GET', 'https://api.example.com/data', false);
            xhr.send();
            window._apiResult = JSON.parse(xhr.responseText);
        """)
        result = ctx.eval("window._apiResult", to_py=True)
        print(f"  XHR 响应: {result}")
        # 查看 netLog
        entries = ctx.eval("window.__iv8__.netLog.entries", to_py=True)
        for e in entries:
            print(f"  netLog: {e.get('method','')} {e.get('url','')}")

def demo_event_dispatch():
    """6. 可信输入事件"""
    print("\n" + "=" * 60)
    print("6. 可信输入事件 (isTrusted=true)")
    print("=" * 60)
    with iv8.JSContext() as ctx:
        ctx.eval("""
            window.__iv8__.page.load({
                baseURL: 'https://example.com',
                html: '<html><body><button id="btn">Click</button></body></html>'
            });
            var clickInfo = null;
            document.getElementById('btn').addEventListener('click', e => {
                clickInfo = {isTrusted: e.isTrusted, type: e.type, x: e.clientX, y: e.clientY};
            });
        """)
        ctx.eval("""
            window.__iv8__.input.dispatchMouseEvent({
                type: 'click',
                target: document.getElementById('btn'),
                clientX: 50, clientY: 25,
                button: 0, buttons: 0
            });
        """)
        info = ctx.eval("clickInfo", to_py=True)
        print(f"  事件信息: {info}")

def demo_wrap_native():
    """7. 函数伪装"""
    print("\n" + "=" * 60)
    print("7. 函数伪装 wrapNative")
    print("=" * 60)
    with iv8.JSContext() as ctx:
        ctx.eval("""
            var myFunc = window.__iv8__.wrapNative(function(x) { return x * 2; }, 'myFunc');
        """)
        print(f"  toString: {ctx.eval('myFunc.toString()')}")
        print(f"  调用结果: {ctx.eval('myFunc(21)')}")

def demo_python_js_interop():
    """8. Python <-> JS 互调"""
    print("\n" + "=" * 60)
    print("8. Python <-> JS 互调")
    print("=" * 60)
    with iv8.JSContext() as ctx:
        # 暴露 Python 函数到 JS
        def add(a, b):
            return a + b
        ctx.expose(add)

        # 暴露数据
        ctx.expose({"token": "abc123", "debug": True}, "config")

        result = ctx.eval("__iv8__.data.add(10, 20)")
        print(f"  JS调Python add(10,20): {result}")
        token = ctx.eval("__iv8__.data.config.token")
        print(f"  JS读Python config.token: {token}")

        # Python 调用 JS
        ctx.eval("function jsMultiply(a, b) { return a * b; }")
        # 通过 eval 直接调用
        print(f"  Python调JS: {ctx.eval('jsMultiply(6, 7)')}")

def demo_crypto():
    """9. Web Crypto API"""
    print("\n" + "=" * 60)
    print("9. Web Crypto API")
    print("=" * 60)
    with iv8.JSContext() as ctx:
        # getRandomValues
        ctx.eval("""
            var arr = new Uint8Array(16);
            crypto.getRandomValues(arr);
            window._randomBytes = Array.from(arr);
        """)
        rnd = ctx.eval("window._randomBytes", to_py=True)
        print(f"  getRandomValues (16 bytes): {rnd[:8]}...")

        # SHA-256
        ctx.eval("""
            async function sha256(message) {
                const msgBuffer = new TextEncoder().encode(message);
                const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
                return Array.from(new Uint8Array(hashBuffer));
            }
            window._hashResult = null;
            sha256('hello iv8').then(h => { window._hashResult = h; });
            window.__iv8__.eventLoop.drainMicrotasks();
        """)
        h = ctx.eval("window._hashResult", to_py=True)
        if h:
            print(f"  SHA-256('hello iv8'): {''.join(f'{b:02x}' for b in h)}")

def demo_async():
    """10. async/await + Promise"""
    print("\n" + "=" * 60)
    print("10. async/await + Promise")
    print("=" * 60)
    with iv8.JSContext(time_mode="logical") as ctx:
        ctx.eval("""
            window._asyncResult = null;
            async function fetchData() {
                const resp = await Promise.resolve({data: [1,2,3]});
                return resp.data;
            }
            fetchData().then(d => { window._asyncResult = d; });
            window.__iv8__.eventLoop.drainMicrotasks();
        """)
        result = ctx.eval("window._asyncResult", to_py=True)
        print(f"  async 结果: {result}")

def demo_debug_mode():
    """11. debug 模式 API 监控"""
    print("\n" + "=" * 60)
    print("11. debug 模式 API 监控")
    print("=" * 60)
    with iv8.JSContext(mode='debug') as ctx:
        ctx.eval("""
            var ua = navigator.userAgent;
            var lang = navigator.language;
            document.title = 'test';
        """)
        print("  debug 模式已启用, API 调用被记录")
        print("  (完整日志需配合 DevTools 查看)")

def demo_multithread():
    """12. 多线程并行"""
    print("\n" + "=" * 60)
    print("12. 多线程并行")
    print("=" * 60)
    results = {}
    def run_js(thread_id, ua):
        with iv8.JSContext(environment={"navigator": {"userAgent": ua}}) as ctx:
            val = ctx.eval("""
                var sum = 0;
                for(var i = 0; i < 100000; i++) sum += Math.sin(i);
                sum;
            """)
            results[thread_id] = round(val, 4)

    start = time.time()
    threads = []
    for i in range(4):
        t = threading.Thread(target=run_js, args=(i, f"ThreadBot/{i}"))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start

    for tid, val in sorted(results.items()):
        print(f"  Thread {tid}: result={val}")
    print(f"  4线程总耗时: {elapsed:.3f}s")

def demo_html_innerhtml():
    """13. innerHTML 快速加载"""
    print("\n" + "=" * 60)
    print("13. innerHTML 快速加载 (轻量级)")
    print("=" * 60)
    with iv8.JSContext() as ctx:
        ctx.eval("""
            document.documentElement.innerHTML = `
                <head><title>Fast Page</title></head>
                <body>
                    <div id="content">
                        <p>Paragraph 1</p>
                        <p>Paragraph 2</p>
                    </div>
                </body>
            `;
        """)
        print(f"  title: {ctx.eval('document.title')}")
        print(f"  paras: {ctx.eval('document.querySelectorAll(\"p\").length')}")

if __name__ == "__main__":
    print(f"iv8 version: {iv8.__version__}" if hasattr(iv8, '__version__') else "iv8 installed")
    print()

    demo_basic_eval()
    demo_browser_env()
    demo_dom()
    demo_event_loop()
    demo_network()
    demo_event_dispatch()
    demo_wrap_native()
    demo_python_js_interop()
    demo_crypto()
    demo_async()
    demo_debug_mode()
    demo_multithread()
    demo_html_innerhtml()

    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)
