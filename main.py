"""
main.py — lightweight app launcher
Now `main.py` only wires routers, static assets and lifecycle events; business logic lives in modules.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from routes import router
from http_client import get_http_client, close_http_client

app = FastAPI(title="Steam Price Search API")

# Include API routes
app.include_router(router)

# Serve static frontend
app.mount('/static', StaticFiles(directory='static'), name='static')

@app.get('/', response_class=HTMLResponse)
async def root():
    with open('static/index.html', 'r', encoding='utf-8') as f:
        return f.read()


@app.on_event("startup")
async def on_startup():
    # ensure shared HTTP client exists
    await get_http_client()


@app.on_event("shutdown")
async def on_shutdown():
    await close_http_client()


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

