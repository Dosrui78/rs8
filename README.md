# RS8 — 瑞数反爬绕过框架

基于 iv8 的通用瑞数反爬绕过工具，无需浏览器，轻量快速。

## 安装

```bash
uv sync
```

## 使用

### Web 模式（默认）

```bash
python main.py
```

打开 `http://127.0.0.1:3333` 使用 Web UI。

### CLI 模式

```bash
python main.py --cli
```

输入 URL 即可，输出 Cookie 和 cURL 命令。

### REST API

```bash
curl -X POST http://localhost:3333/api/bypass \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/protected/page"}'
```

返回：

```json
{
  "success": true,
  "cookie": "__jsl_clearance=xxx",
  "curl": "curl 'https://...' -H 'cookie: ...'",
  "elapsed": 3.21
}
```

其他端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/profiles` | 可用指纹列表 |
| GET | `/api/health` | 健康检查 |

### API 请求参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `url` | string | **必填** 目标 URL |
| `profile` | string | 浏览器指纹，默认 `chrome_136` |
| `proxy` | string | HTTP 代理 |
| `headers` | object | 自定义请求头 |

## 浏览器指纹

内置 `chrome_136`（默认）、`chrome_130`、`chrome_124`、`firefox_136`、`edge_130`。在 `profiles/` 下添加 `{browser}_{version}.py` 可自定义。

## 站点配置

`recipes/` 下创建 `.py` 文件，配置特定站点行为：

```python
from recipes.base import Recipe

recipe = Recipe(
    domain="*.example.com",
    max_rounds=2,
)
```

## 配置

编辑 `config.py`：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `HOST` | `127.0.0.1` | 监听地址 |
| `PORT` | `3333` | 端口 |
| `REQUEST_TIMEOUT` | `30` | 超时秒数 |
