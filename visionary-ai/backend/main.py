"""
backend/main.py
Visionary AI — Backend Proxy Server
Connects the frontend to the Colab GPU model server.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import os
import time
import logging
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# ── Config ──────────────────────────────────────────────────────
COLAB_API_URL = os.getenv("COLAB_API_URL", "")
MAX_HISTORY   = int(os.getenv("MAX_HISTORY", 10))
RATE_LIMIT    = int(os.getenv("RATE_LIMIT_PER_MINUTE", 20))

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Simple in-memory rate limiter ────────────────────────────────
_request_counts: dict[str, list] = defaultdict(list)

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    window = 60  # 1 minute
    _request_counts[ip] = [t for t in _request_counts[ip] if now - t < window]
    if len(_request_counts[ip]) >= RATE_LIMIT:
        return True
    _request_counts[ip].append(now)
    return False

# ── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Visionary AI — Backend",
    description="Proxy server for multimodal AI generation (text, image, video)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# ── Schemas ──────────────────────────────────────────────────────
class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000)
    history: list = []
    style_hint: Optional[str] = None   # e.g. "cinematic", "anime", "photorealistic"
    num_frames: Optional[int] = 8      # for video: how many frames


class FeedbackRequest(BaseModel):
    prompt: str
    result_type: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


# ── Routes ──────────────────────────────────────────────────────
@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "colab_configured": bool(COLAB_API_URL),
        "rate_limit_per_min": RATE_LIMIT,
        "max_history_messages": MAX_HISTORY,
    }


@app.get("/api/colab-status")
async def colab_status():
    """Ping the Colab model server and return its health."""
    if not COLAB_API_URL:
        return {"online": False, "reason": "COLAB_API_URL not configured"}
    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        try:
            r = await client.get(f"{COLAB_API_URL}/health")
            info = r.json()
            return {"online": True, "models": info.get("models_loaded", {})}
        except Exception as e:
            return {"online": False, "reason": str(e)}


@app.post("/api/generate")
async def generate(request: PromptRequest, req: Request):
    """Forward a generation request to the Colab model server."""
    client_ip = req.client.host

    # Rate limiting
    if is_rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")

    if not COLAB_API_URL:
        raise HTTPException(
            status_code=503,
            detail="COLAB_API_URL not set. Add it to your .env file and restart the server."
        )

    # Trim history to avoid oversized payloads
    trimmed_history = request.history[-(MAX_HISTORY):]

    payload = {
        "prompt": request.prompt,
        "history": trimmed_history,
        "style_hint": request.style_hint,
        "num_frames": request.num_frames,
    }

    logger.info(f"[{client_ip}] Prompt: {request.prompt[:80]}...")

    async with httpx.AsyncClient(timeout=600.0, verify=False) as client:
        try:
            response = await client.post(f"{COLAB_API_URL}/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"[{client_ip}] Result type: {result.get('type')} ✓")
            return result

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="Cannot reach Colab model server. Make sure your notebook is running and the ngrok URL is correct."
            )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Model server timed out (generation can take 1–3 min). Try again."
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))


@app.post("/api/feedback")
async def feedback(fb: FeedbackRequest):
    """Collect user feedback (logged server-side; extend to DB as needed)."""
    logger.info(
        f"[Feedback] type={fb.result_type} rating={fb.rating}/5 "
        f"prompt={fb.prompt[:60]} comment={fb.comment}"
    )
    return {"received": True}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
