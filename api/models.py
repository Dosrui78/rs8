from pydantic import BaseModel
from typing import Optional


class BypassRequest(BaseModel):
    url: str
    profile: str = "chrome_136"
    proxy: Optional[str] = None
    headers: dict = {}


class BypassResponse(BaseModel):
    success: bool
    cookie: str = ""
    cookie_dict: dict = {}
    curl: str = ""
    version: str = ""
    elapsed: float = 0.0
    error: str = ""
    logs: list = []
