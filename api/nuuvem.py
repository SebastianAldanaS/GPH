from typing import List, Optional, Dict
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, quote_plus
from http_client import get_http_client
from utils import _normalize_text, _similar

_nuuvem_cache: Dict[str, object] = {"data": {}, "ts": {}}
NUUVEM_CACHE_TTL = 10 * 60


async def nuuvem_search_v2(query: str, limit: int = 5, locale: str = "co-es") -> List[dict]:
    client = await get_http_client()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "es-ES,es;q=0.9"}

    q = query.strip()
    path_q = quote_plus(q)
    urls_to_try = [f"https://www.nuuvem.com/{locale}/catalog/page/1/search/{path_q}",
                   f"https://www.nuuvem.com/store/search?q={path_q}"]

    results: List[dict] = []
    qnorm = _normalize_text(query)

    for url in urls_to_try:
        try:
            r = await client.get(url, headers=headers, timeout=10.0)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

            products = soup.select("div.nvm-grid > div > a, .productCard, .card, .product-item, a.product-item") or []

            for a in products:
                if len(results) >= limit:
                    break
                name_el = a.select_one("h3.game-card__product-name") or a.select_one("h3") or a.select_one('.productCard-title') or a.select_one('.card-title')
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if _similar(qnorm, _normalize_text(name)) < 0.45:
                    continue

                price_el = a.select_one(".product-price--val span:not(.product-price--old)") or a.select_one(".add-to-cart__btn__text") or a.select_one('.product-price__price') or a.select_one('.productCard-price')
                precio = None
                moneda = None
                if price_el:
                    txt = price_el.get_text(" ", strip=True)
                    m = re.search(r"(COL\$|R\$|U\$S|USD|\$)?\s*([0-9.,]+)", txt, re.I)
                    if m:
                        moneda = (m.group(1) or '').strip()
                        num = m.group(2).replace('.', '').replace(',', '.')
                        try:
                            precio = float(num)
                        except Exception:
                            precio = None

                img = None
                img_el = a.select_one('img')
                if img_el and img_el.get('src'):
                    img = img_el.get('src')

                href = a.get('href') or ''
                full = href if href.startswith('http') else urljoin('https://www.nuuvem.com', href)

                results.append({
                    'nombre': name,
                    'url': full,
                    'tiny_image': img or '',
                    'precio_detectado': precio,
                    'moneda': moneda,
                })

            if len(results) >= limit:
                break
        except Exception:
            continue

    return results


async def nuuvem_fetch_v2(product: dict) -> Optional[dict]:
    url = product.get('url')
    client = await get_http_client()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "es-ES,es;q=0.9"}

    try:
        r = await client.get(url, headers=headers, timeout=10.0)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')

        price_el = soup.select_one('.product-price--val span:not(.product-price--old)') or soup.select_one('.product-price__price')
        precio = None
        moneda = None
        if price_el:
            txt = price_el.get_text(' ', strip=True)
            m = re.search(r"(COL\$|R\$|U\$S|USD|\$)?\s*([0-9.,]+)", txt, re.I)
            if m:
                moneda = (m.group(1) or '').strip()
                num = m.group(2).replace('.', '').replace(',', '.')
                try:
                    precio = float(num)
                except Exception:
                    precio = None

        og = soup.find('meta', property='og:image')
        tiny = og.get('content') if og and og.get('content') else product.get('tiny_image') or ''
        name_tag = soup.find('h1') or soup.find('h2')
        nombre = name_tag.get_text(strip=True) if name_tag else product.get('nombre')

        return {
            'nombre': nombre,
            'precio_final': precio,
            'moneda': moneda,
            'tiny_image': tiny or '',
            'url': url,
        }
    except Exception:
        return None