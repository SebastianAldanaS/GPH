from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.google.com/"
}

def get_nuuvem(game):
    url = f"https://www.nuuvem.com/co-es/catalog/search/{game.replace(' ', '%20')}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    card = soup.select_one(".product-card")
    if not card:
        return None

    return {
        "store": "Nuuvem",
        "name": card.select_one(".product-title").text.strip(),
        "price": card.select_one(".price--highlight").text.strip()
    }

def get_humble(game):
    url = f"https://www.humblebundle.com/store/search?search={game.replace(' ', '%20')}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    card = soup.select_one(".entity-product-tile")
    if not card:
        return None

    return {
        "store": "Humble",
        "name": card.select_one(".entity-title").text.strip(),
        "price": card.select_one(".price").text.strip()
    }

def get_fanatical(game):
    url = f"https://www.fanatical.com/es/search?search={game.replace(' ', '%20')}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    card = soup.select_one("a.product-grid-tile")
    if not card:
        return None

    return {
        "store": "Fanatical",
        "name": card.select_one(".product-title").text.strip(),
        "price": card.select_one(".price").text.strip()
    }

@app.get("/prices")
def get_prices(game: str):
    return {
        "nuuvem": get_nuuvem(game),
        "humble": get_humble(game),
        "fanatical": get_fanatical(game)
    }

