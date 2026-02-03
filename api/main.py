import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.routes import router

# Carpeta api (donde está main.py); los estáticos están en api/static
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Orígenes permitidos (siempre incluir el front en Vercel)
_CORS_ORIGINS_RAW = os.environ.get("CORS_ORIGINS", "").strip()
if _CORS_ORIGINS_RAW == "*":
    _ALLOWED_ORIGINS = {"*"}
else:
    _ALLOWED_ORIGINS = {o.strip() for o in _CORS_ORIGINS_RAW.split(",") if o.strip()}
if not _ALLOWED_ORIGINS or (_CORS_ORIGINS_RAW != "*" and not _ALLOWED_ORIGINS):
    _ALLOWED_ORIGINS = {
        "https://gph-six.vercel.app",
        "https://www.gph-six.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8080",
    }

_CORS_HEADERS = {
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Max-Age": "86400",
}


class CorsMiddleware(BaseHTTPMiddleware):
    """Añade CORS a todas las respuestas para que el front en Vercel pueda llamar al API."""

    async def dispatch(self, request: Request, call_next) -> Response:
        origin = request.headers.get("origin", "").strip()
        if _ALLOWED_ORIGINS == {"*"}:
            allow_origin = "*"
            cors_headers = {**_CORS_HEADERS, "Access-Control-Allow-Origin": "*"}
        elif origin and origin in _ALLOWED_ORIGINS:
            allow_origin = origin
            cors_headers = {
                **_CORS_HEADERS,
                "Access-Control-Allow-Origin": allow_origin,
                "Access-Control-Allow-Credentials": "true",
            }
        else:
            allow_origin = next(iter(_ALLOWED_ORIGINS), "")
            cors_headers = {
                **_CORS_HEADERS,
                "Access-Control-Allow-Origin": allow_origin,
                "Access-Control-Allow-Credentials": "true",
            }

        if request.method == "OPTIONS":
            return Response(status_code=200, headers=cors_headers)

        response = await call_next(request)
        for key, value in cors_headers.items():
            response.headers[key] = value
        return response


app = FastAPI(title="Steam Price Search API")

# Middleware CORS como primera capa para que todas las respuestas lleven los headers
app.add_middleware(CorsMiddleware)

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
