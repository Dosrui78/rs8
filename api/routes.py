import json
import os
from fastapi import APIRouter, HTTPException
from api.models import BypassRequest, BypassResponse
from core.pipeline import Pipeline, PipelineConfig
from core.curl import format_curl

router = APIRouter()


@router.post("/api/bypass", response_model=BypassResponse)
async def bypass(req: BypassRequest):
    cfg = PipelineConfig(
        url=req.url,
        profile=req.profile,
        proxy=req.proxy,
        headers=req.headers,
    )
    p = Pipeline()
    result = p.run(req.url, cfg)

    resp = BypassResponse(
        success=result.success,
        cookie=result.cookie,
        cookie_dict=result.cookie_dict,
        version=result.version,
        elapsed=result.elapsed,
        error=result.error,
        logs=result.logs,
    )

    if result.success:
        resp.curl = format_curl(req.url, result.cookie)

    return resp


@router.get("/api/profiles")
async def list_profiles():
    profiles_dir = os.path.join(os.path.dirname(__file__), "..", "profiles")
    browsers = {"chrome": "Chrome", "firefox": "Firefox", "edge": "Edge"}
    names = []
    for f in os.listdir(profiles_dir):
        for prefix, label in browsers.items():
            if f.startswith(f"{prefix}_") and f.endswith(".py"):
                ver = f.replace(f"{prefix}_", "").replace(".py", "")
                names.append({"id": f.replace(".py", ""), "label": f"{label} {ver}"})
    return {"profiles": sorted(names, key=lambda x: x["label"])}


@router.get("/api/health")
async def health():
    return {"status": "ok"}
