import re
import json
import logging
from typing import List, Dict
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from api.http_client import get_http_client
from api.utils import _normalize_text, _similar

BASE_URL = "https://www.greenmangaming.com"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"}

logger = logging.getLogger(__name__)




async def _extract_from_page_text(text: str) -> Dict:
    try:
        soup = BeautifulSoup(text, "lxml")

        def _parse_price_text(t: str):
            if not t:
                return None
            s = re.sub(r"[^\d]", "", t)  # solo números (COP)
            try:
                return float(s)
            except:
                return None

        # 🔹 Precios GMG
        el_cur = soup.select_one('gmgprice[type="currentPrice"]')
        el_rrp = soup.select_one('gmgprice[type="rrp"]')

        precio = _parse_price_text(el_cur.text) if el_cur and el_cur.text.strip() else None
        precio_original = _parse_price_text(el_rrp.text) if el_rrp and el_rrp.text.strip() else None

        # 🔹 Si no hay descuento real, ignorar RRP
        porcentaje = 0
        if precio_original and precio and precio_original > precio:
            porcentaje = int(round((1 - (precio / precio_original)) * 100))
        else:
            precio_original = None

        # 🔹 Nombre
        name = None
        h1 = soup.select_one("h1")
        if h1:
            name = h1.get_text(strip=True)

        if not name and soup.title:
            name = soup.title.string.split(" - ")[0]

        # 🔹 Imagen
        thumb = ""
        img = soup.select_one('meta[property="og:image"]')
        if img and img.get("content"):
            thumb = img["content"]

        if not precio:
            return {}

        return {
            "nombre": name,
            "precio": precio,
            "moneda": "COP",
            "precio_original": precio_original,
            "porcentaje_descuento": porcentaje,
            "url": None,
            "tiny_image": thumb
        }

    except Exception as e:
        print("GMG parse error:", e)
        return {}


async def gmg_search(q: str, limit: int = 3) -> List[Dict]:
    client = await get_http_client()

    slug = re.sub(r"[^\w\s]", "", (q or "").lower()).strip()
    slug = re.sub(r"\s+", "-", slug)

    candidate_urls = [
        f"{BASE_URL}/es/games/{slug}-pc/",
        f"{BASE_URL}/games/{slug}-pc/",
        f"{BASE_URL}/es/games/{slug}/",
        f"{BASE_URL}/games/{slug}/",
    ]

    for url in candidate_urls:
        try:
            r = await client.get(url, headers=HEADERS, timeout=10.0)
            if 200 <= r.status_code < 500:
                info = await _extract_from_page_text(r.text)
                if info and info.get("precio") is not None:
                    info["tienda"] = "GreenManGaming"
                    info["url"] = url
                    return [info]
        except Exception as e:
            logger.debug("GMG direct fetch failed for %s: %s", url, e)

    # 🔁 Fallback búsqueda
    try:
        search_url = f"{BASE_URL}/es/search/?query={quote_plus(q)}"
        r = await client.get(search_url, headers=HEADERS, timeout=10.0)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "lxml")
        items = soup.select("a.product-item") or []

        results = []
        for a in items[:limit]:
            href = a.get("href")
            if not href:
                continue

            full = href if href.startswith("http") else BASE_URL + href

            try:
                rr = await client.get(full, headers=HEADERS, timeout=10.0)
                if 200 <= rr.status_code < 500:
                    info = await _extract_from_page_text(rr.text)
                    if info and info.get("precio") is not None:
                        info["tienda"] = "GreenManGaming"
                        info["url"] = full
                        results.append(info)
            except:
                continue

        return results

    except Exception as e:
        logger.debug("GMG search fetch failed: %s", e)
        return []
