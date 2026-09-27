"""FastAPI service for TARA — Transformer-based Audio & Response Assistant."""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import APP_NAME, APP_FULL_NAME, APP_TAGLINE, CONFIDENCE_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tara")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TARA backend...")
    try:
        from predict import _artifacts
        _artifacts()
        logger.info("Deep Learning Transformer model, tokenizer, and labels loaded successfully.")
    except Exception as err:
        logger.warning(f"Model preload warning: {err}")
    yield
    logger.info("Shutting down TARA backend.")


app = FastAPI(title=APP_FULL_NAME, version="2.0.0", lifespan=lifespan)

# Allowed browser origins. Defaults cover local Next.js dev (localhost and
# 127.0.0.1 on port 3000) plus the production Vercel frontend. Override per
# environment with CORS_ORIGINS (comma-separated), e.g. on Render:
#   CORS_ORIGINS=https://tara-ai-chatbot.vercel.app
DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://tara-ai-chatbot.vercel.app",
]

origins_env = os.getenv("CORS_ORIGINS", "").strip()
origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()] or list(DEFAULT_CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    message: str | None = Field(default=None, description="The chatbot question.")
    text: str | None = Field(default=None, description="Legacy name for the chatbot question.")
    session_id: str | None = Field(default=None, description="Session ID for conversation context.")

    @property
    def user_text(self) -> str:
        return self.message if isinstance(self.message, str) else (self.text or "")


@app.get("/")
def root() -> dict:
    return {
        "app": APP_NAME,
        "full_name": APP_FULL_NAME,
        "tagline": APP_TAGLINE,
        "docs": {"health": "GET /health", "predict": "POST /predict", "history": "GET /history?session_id=..."},
    }


@app.get("/health")
def health() -> dict:
    from predict import model_ready

    ready = model_ready()
    if not ready:
        raise HTTPException(
            status_code=503,
            detail={"status": "model_missing", "app": APP_NAME, "model_ready": False},
        )
    return {"status": "ok", "app": APP_NAME, "model_ready": True}


@app.post("/predict")
def predict_route(payload: PredictRequest) -> dict:
    text = payload.user_text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="JSON body must include a non-empty 'message' or 'text' string."
        )

    session_id = payload.session_id or str(uuid.uuid4())

    from predict import predict_intent

    try:
        result = predict_intent(text, session_id=session_id)
        result["app"] = APP_NAME
        result["threshold"] = CONFIDENCE_THRESHOLD
        result["session_id"] = session_id
        return result
    except Exception as exc:
        logger.error(f"Prediction failed for query '{text}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Intent prediction failed on the server. Please try again."
        )


@app.get("/history")
def get_history(session_id: str = Query(..., description="Session ID")) -> dict:
    try:
        from db.repository import get_repository
        repo = get_repository()
        records = repo.get_history(session_id, limit=50)
        return {
            "session_id": session_id,
            "messages": [r.to_dict() for r in records],
        }
    except Exception as exc:
        logger.error(f"History retrieval failed: {exc}", exc_info=True)
        return {"session_id": session_id, "messages": []}


if __name__ == "__main__":
    import uvicorn

    # Local dev default is 8000 (matches frontend/.env.local).
    # Render/Procfile pass $PORT explicitly, so deployment is unaffected.
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)

