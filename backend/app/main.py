from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.api.routes import stores, analysis, batch, browse

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stores.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(batch.router, prefix="/api/v1")
app.include_router(browse.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- 静的フロントエンド配信 ---
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
