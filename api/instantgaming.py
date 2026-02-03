import re
import logging
from typing import List, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from api.http_client import get_http_client
from api.utils import _normalize_text, _similar

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES,es;q=0.9"}


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


def _titulo_similar(a: str, b: str, thresh: float = 0.5) -> bool:
    na = _normalize_text(a)
    nb = _normalize_text(b)
    # Accept when query tokens appear in title (helps with short queries)
    if na and na in nb:
        return True
    # fallback to similarity threshold
    return _similar(na, nb) >= thresh


async def instantgaming_search(nombre_juego: str, limit: int = 5) -> List[Dict]:
    """Search Instant Gaming for a game and return candidate price info.

    Returns list of dicts with keys similar to other store modules:
    ['nombre','precio','moneda','precio_original','porcentaje_descuento','url','tiny_image','tienda']
    """
    client = await get_http_client()
    try:
        nombre_limpio = _normalize_text(nombre_juego)
        query = quote_plus(nombre_limpio)
        # Use the simpler query parameter; additional filters may return JS-heavy pages
        url = f"https://www.instant-gaming.com/es/busquedas/?query={query}"


        r = await client.get(url, headers=HEADERS, timeout=10.0)
        if not (200 <= r.status_code < 500):
            return []

        soup = BeautifulSoup(r.text, 'lxml')
        productos = soup.select('article.item')[:limit]
        resultados = []

        for producto in productos:
            # Title is stored on the cover link's title attribute (e.g., 'comprar The Witcher 3...')
            cover = producto.select_one('a.cover')
            if not cover:
                continue
            nombre = cover.get('title', '').strip()
            if not nombre:
                continue

            # strip leading 'comprar ' from Instant Gaming titles
            if nombre.lower().startswith('comprar '):
                nombre = nombre[7:].strip()

            if not _titulo_similar(nombre_limpio, nombre):
                continue

            href = cover.get('href')
            if not href:
                continue
            url_producto = href if href.startswith('http') else f"https://www.instant-gaming.com{href}"

            precio_el = producto.select_one('div.price') or producto.select_one('.price-row .price')
            precio_text = precio_el.get_text(strip=True) if precio_el else ''

            precio_val = _parse_price_text(precio_text)
            moneda = 'EUR' if '€' in (precio_text or '') else None

            if precio_val is None:
                # skip items without a parseable price
                continue

            # try to detect a struck-through original price inside same block
            precio_original = None
            porcentaje = 0
            rr = producto.select_one('.old-price, .discount-price, .price-old')
            if rr:
                rr_text = rr.get_text(strip=True)
                precio_original = _parse_price_text(rr_text)
                if precio_original and precio_original > precio_val:
                    try:
                        porcentaje = int(round((1 - (precio_val / precio_original)) * 100))
                    except Exception:
                        porcentaje = 0

            tiny_image = ''
            img = producto.select_one('img')
            if img:
                tiny_image = img.get('data-src') or img.get('src') or ''

            resultados.append({
                'nombre': nombre,
                'precio': precio_val,
                'moneda': moneda,
                'precio_original': precio_original,
                'porcentaje_descuento': porcentaje,
                'url': url_producto,
                'tiny_image': tiny_image or '',
                'tienda': 'Instant Gaming'
            })

        logger.debug('Instant Gaming: parsed %s results for query=%s', len(resultados), nombre_juego)
        return resultados
    except Exception as e:
        logger.debug('Instant Gaming search failed: %s', e)
        return []
