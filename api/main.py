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

# CORS: necesario cuando el front está en Vercel y el back en Railway
# CORS_ORIGINS puede ser "https://tu-app.vercel.app" o "*" para desarrollo
_cors_origins = os.environ.get("CORS_ORIGINS", "").strip() or "*"
_origins_list = ["*"] if _cors_origins == "*" else [o.strip() for o in _cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins_list,
    allow_credentials=(_cors_origins != "*"),  # con "*" el navegador no permite credentials
    allow_methods=["*"],
    allow_headers=["*"],
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
