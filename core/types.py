from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExtractedData:
    """从 HTML 中提取的瑞数参数"""
    version: str = ""
    meta_content: str = ""
    meta_r: str = "m"
    ts_js: str = ""
    auto_script_url: str = ""
    auto_script_js: str = ""
    features: dict = field(default_factory=dict)
    extra_hooks: list[str] = field(default_factory=list)  # recipe hooks


@dataclass
class BypassResult:
    """一次 bypass 的结果"""
    success: bool = False
    cookie: str = ""
    cookie_dict: dict = field(default_factory=dict)
    version: str = ""
    elapsed: float = 0.0
    logs: list = field(default_factory=list)
    error: str = ""


@dataclass
class PipelineConfig:
    url: str = ""
    profile: str = "chrome_136"
    proxy: Optional[str] = None
    headers: dict = field(default_factory=dict)
    timeout: int = 30
