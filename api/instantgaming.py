import re
import logging
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from api.http_client import get_http_client
from api.utils import _normalize_text, _similar

try:
    import lxml  # noqa: F401
    _BS_PARSER = "lxml"
except ImportError:
    _BS_PARSER = "html.parser"

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def _parse_price_text(t: str):
    if not t:
        return None
    s = t.strip()
    # remove currency symbols and keep digits, dots and commas
    s = ''.join(ch for ch in s if ch.isdigit() or ch in '.,')
    if not s:
        return None

    # Instant Gaming uses comma as decimal separator in many locales (e.g. '1,99')
    if ',' in s and '.' not in s:
        s = s.replace('.', '').replace(',', '.')
    elif '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    elif '.' in s and ',' not in s:
        parts = s.split('.')
        if len(parts) > 1 and len(parts[-1]) == 3:
            s = s.replace('.', '')
    try:
        return float(s)
    except Exception:
        return None


def _titulo_similar(a: str, b: str, thresh: float = 0.35) -> bool:
    na = _normalize_text(a)
    nb = _normalize_text(b)
    if not na or not nb:
        return False
    if na in nb:
        return True
    # Que las palabras significativas de la query estén en el título
    words = [w for w in na.split() if len(w) >= 2]
    if words and sum(1 for w in words if w in nb) >= max(1, len(words) * 0.6):
        return True
    return _similar(na, nb) >= thresh


async def instantgaming_search(nombre_juego: str, limit: int = 5) -> List[Dict]:
    """Search Instant Gaming for a game and return candidate price info."""
    client = await get_http_client()
    try:
        nombre_limpio = _normalize_text(nombre_juego)
        # Buscar con el nombre original (puede tener más resultados)
        query = quote_plus(nombre_juego.strip())
        urls_to_try = [
            f"https://www.instant-gaming.com/es/busquedas/?query={query}",
            f"https://www.instant-gaming.com/en/search/?query={query}",
        ]
        resultados = []
        for url in urls_to_try:
            r = await client.get(url, headers=HEADERS, timeout=15.0)
            if not (200 <= r.status_code < 500):
                continue
            soup = BeautifulSoup(r.text, _BS_PARSER)
            # Varios selectores por si cambió la estructura
            productos = (
                soup.select("article.item")
                or soup.select("article[class*='item']")
                or soup.select("[data-product]")
                or soup.select(".game-item")
                or []
            )
            productos = productos[: limit * 2]

            for producto in productos:
                if len(resultados) >= limit:
                    break
                cover = (
                    producto.select_one("a.cover")
                    or producto.select_one("a[href*='/es/']")
                    or producto.select_one("a[href*='/en/']")
                    or producto.select_one("a")
                )
                if not cover:
                    continue
                nombre = (cover.get("title") or "").strip()
                if not nombre:
                    name_el = producto.select_one("h2") or producto.select_one("h3") or producto.select_one("[class*='title']")
                    nombre = name_el.get_text(strip=True) if name_el else ""
                if not nombre:
                    continue
                if nombre.lower().startswith("comprar "):
                    nombre = nombre[7:].strip()

                if not _titulo_similar(nombre_limpio, nombre):
                    continue

                href = cover.get("href")
                if not href:
                    continue
                url_producto = href if href.startswith("http") else f"https://www.instant-gaming.com{href}"

                precio_el = (
                    producto.select_one("div.price")
                    or producto.select_one(".price-row .price")
                    or producto.select_one("[class*='price']")
                )
                precio_text = precio_el.get_text(strip=True) if precio_el else ""
                precio_val = _parse_price_text(precio_text)
                if precio_val is None:
                    continue
                moneda = "EUR" if "€" in (precio_text or "") else "EUR"

                precio_original = None
                porcentaje = 0
                rr = producto.select_one(".old-price, .discount-price, .price-old, [class*='old']")
                if rr:
                    precio_original = _parse_price_text(rr.get_text(strip=True))
                    if precio_original and precio_original > precio_val:
                        try:
                            porcentaje = int(round((1 - (precio_val / precio_original)) * 100))
                        except Exception:
                            pass

                img = producto.select_one("img")
                tiny_image = (img.get("data-src") or img.get("src") or "") if img else ""

                resultados.append({
                    "nombre": nombre,
                    "precio": precio_val,
                    "moneda": moneda,
                    "precio_original": precio_original,
                    "porcentaje_descuento": porcentaje,
                    "url": url_producto,
                    "tiny_image": tiny_image,
                    "tienda": "Instant Gaming",
                })
            if resultados:
                break

        return resultados[:limit]
    except Exception as e:
        logger.debug("Instant Gaming search failed: %s", e)
        return []
