from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routes import router

app = FastAPI(title="RS8 - 瑞数通杀", version="0.1.0")

app.include_router(router)

from pathlib import Path
ui_static = Path(__file__).resolve().parent.parent / "ui" / "static"
if ui_static.exists():
    app.mount("/static", StaticFiles(directory=str(ui_static)), name="static")

ui_templates = Path(__file__).resolve().parent.parent / "ui" / "templates"
if ui_templates.exists():
    from fastapi.responses import HTMLResponse
    index_html = ui_templates / "index.html"

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return index_html.read_text(encoding="utf-8")
