# RS8 — 瑞数通杀框架

基于 iv8 的通用瑞数(Ruishu)反爬绕过框架。输入 URL，输出 Cookie。

## 架构

```
rs8/
├── core/              引擎层，不依赖外部库
│   ├── pipeline.py    主流程: fetch → detect → iv8 → cookie
│   ├── engine.py      iv8 上下文工厂 + 插件管理器
│   ├── env_builder.py URL → location/navigator 环境装配
│   └── types.py       ExtractedData, BypassResult, PipelineConfig
├── detectors/         瑞数版本检测
│   ├── rs6.py         检测 meta + $_ts + auto_script
│   └── auto.py        遍历所有 detector 自动匹配
├── adapters/          版本执行策略
│   └── rs6.py         注入 DOM → 执行 ts_js → auto_script → eventLoop → cookie
├── plugins/           浏览器 API Mock，可插拔
│   ├── canvas.py      Canvas.toDataURL 固定指纹
│   ├── webgl.py       WebGL getParameter 固定
│   ├── wasm.py        WebAssembly 劫持
│   └── worker.py      Worker 拉回主线程
├── profiles/          浏览器指纹配置
│   ├── chrome_124.py
│   ├── chrome_130.py
│   └── chrome_136.py
├── recipes/           站点配方(特化配置)
│   └── ouyeel.py      欧冶 DOM Mock + 环境覆盖
├── api/               FastAPI 接口
│   ├── server.py      应用入口
│   └── routes.py      POST /api/bypass, GET /api/profiles, GET /api/health
├── ui/                前端(零构建)
│   ├── templates/index.html
│   └── static/        style.css + app.js
├── config.py          全局配置
└── main.py            CLI + Server 入口
```

## 运行

```bash
# Web UI
python main.py          → http://localhost:3333

# CLI 模式
python main.py --cli <url>
```

## 增删改指南

### 加新 Browser Profile

`profiles/chrome_xxx.py`，定义一个 `CHROME_XXX` 常量 dict，重启即用。UI 下拉框自动加载。

### 加新站点 Recipe

```python
# recipes/mysite.py
from recipes.base import Recipe, recipe_matcher

recipe_matcher.register(Recipe(
    domain="www.example.com",
    version_hint="rs6",
    before_exec_hooks=["""
        // 这个站的特殊 DOM Mock
        document.getElementById = function(id) { ... };
    """],
    profile_overrides={
        "location": {"href": "https://www.example.com/page"},
        "navigator": {"userAgent": "..."},
    },
))
```

### 加新 Detector (新瑞数版本)

```python
# detectors/rs7.py (假设)
class RS7Detector(BaseDetector):
    name = "rs7"
    def detect(self, html) -> ExtractedData | None:
        ...

# 加入 auto.py 的 _detectors 列表
```

### 加新 Adapter

```python
# adapters/rs7.py
class RS7Adapter(BaseAdapter):
    version = "rs7"
    plugins = ["canvas", "wasm"]
    def execute(self, ctx, data, logs) -> str:
        ...
# 自动注册 (adapter_registry)

adapter_registry.register(RS7Adapter())
```

## 核心原则

1. **Core 层不依赖外部库**(只依赖 iv8)。requests 只在 Pipeline 里用
2. **插件可插拔** — Adapter 声明需要的插件名列表，PluginManager 自动解析依赖顺序
3. **Recipe > 通用逻辑** — 站点特殊处理放 Recipe，不动通用代码
4. **Profile 是纯数据** — 无逻辑，只定义指纹常量
5. **Detector 只提取** — 不执行 JS，只从 HTML 正则提取参数
6. **Adapter 只执行** — 不关心提取逻辑，只负责在 iv8 上下文中跑 JS 拿 cookie
