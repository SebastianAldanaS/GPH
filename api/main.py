from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routes import router

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Steam Price Search API")

app.include_router(router)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return (BASE_DIR / "static" / "index.html").read_text(encoding="utf-8")
