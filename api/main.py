import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import router

# Carpeta api (donde está main.py); los estáticos están en api/static
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Steam Price Search API")

# CORS: necesario cuando el front está en Vercel y el back en Render
# En Render: Environment → CORS_ORIGINS = https://gph-six.vercel.app (o "*" para permitir todos)
_cors_raw = os.environ.get("CORS_ORIGINS", "").strip()
if _cors_raw == "*":
    _origins_list = ["*"]
    _allow_credentials = False
else:
    _origins_list = [o.strip() for o in _cors_raw.split(",") if o.strip()]
    # Si no hay ninguna configurada, permitir el front típico de Vercel para que funcione sin config
    if not _origins_list:
        _origins_list = [
            "https://gph-six.vercel.app",
            "https://www.gph-six.vercel.app",
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5500",
        ]
    _allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins_list,
    allow_credentials=_allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(router)

# Servir estáticos solo si existen (en Railway puede usarse solo la API)
if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def root():
        return (STATIC_DIR / "index.html").read_text(encoding="utf-8")
else:
    @app.get("/")
    async def root():
        return {"message": "Steam Price Search API", "docs": "/docs"}
