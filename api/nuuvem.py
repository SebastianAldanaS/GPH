from typing import List, Optional, Dict
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, quote_plus
from api.http_client import get_http_client
from api.utils import _normalize_text, _similar

try:
    import lxml  # noqa: F401
    _BS_PARSER = "lxml"
except ImportError:
    _BS_PARSER = "html.parser"

_nuuvem_cache: Dict[str, object] = {"data": {}, "ts": {}}
NUUVEM_CACHE_TTL = 10 * 60


def _title_matches_query(query_norm: str, title: str, min_similarity: float = 0.32) -> bool:
    """True si el título coincide con la búsqueda: query contenida en título o similitud suficiente."""
    if not query_norm or not title:
        return False
    title_norm = _normalize_text(title)
    if query_norm in title_norm:
        return True
    # Palabras significativas de la query (mínimo 2 caracteres)
    words = [w for w in query_norm.split() if len(w) >= 2]
    if words and all(w in title_norm for w in words):
        return True
    return _similar(query_norm, title_norm) >= min_similarity


async def nuuvem_search_v2(query: str, limit: int = 5, locale: str = "co-es") -> List[dict]:
    client = await get_http_client()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept-Language": "es-ES,es;q=0.9"}

    q = query.strip()
    path_q = quote_plus(q)
    # Varias URLs y locales por si la búsqueda cambió
    urls_to_try = [
        f"https://www.nuuvem.com/{locale}/catalog/page/1/search/{path_q}",
        f"https://www.nuuvem.com/store/search?q={path_q}",
        f"https://www.nuuvem.com/br-en/catalog/page/1/search/{path_q}",
        f"https://www.nuuvem.com/br-es/catalog/page/1/search/{path_q}",
    ]

    results: List[dict] = []
    qnorm = _normalize_text(query)
    seen_urls = set()

    for url in urls_to_try:
        if len(results) >= limit:
            break
        try:
            r = await client.get(url, headers=headers, timeout=15.0)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, _BS_PARSER)

            # Múltiples selectores: estructura actual puede variar
            products = (
                soup.select("div.nvm-grid > div > a")
                or soup.select("a[href*='/product/']")
                or soup.select(".productCard")
                or soup.select(".card")
                or soup.select(".product-item")
                or soup.select("a.product-item")
                or []
            )

            for a in products:
                if len(results) >= limit:
                    break
                name_el = (
                    a.select_one("h3.game-card__product-name")
                    or a.select_one("h3")
                    or a.select_one(".productCard-title")
                    or a.select_one(".card-title")
                    or a.select_one("[class*='title']")
                    or a.select_one("[class*='name']")
                )
                name = name_el.get_text(strip=True) if name_el else (a.get("title") or "")
                if not name:
                    continue
                if not _title_matches_query(qnorm, name):
                    continue

                href = (a.get("href") or "").strip()
                if not href or href.startswith("#"):
                    continue
                full = href if href.startswith("http") else urljoin("https://www.nuuvem.com", href)
                if full in seen_urls:
                    continue
                seen_urls.add(full)

                price_el = (
                    a.select_one(".product-price--val span:not(.product-price--old)")
                    or a.select_one(".add-to-cart__btn__text")
                    or a.select_one(".product-price__price")
                    or a.select_one(".productCard-price")
                    or a.select_one("[class*='price']")
                )
                precio = None
                moneda = None
                if price_el:
                    txt = price_el.get_text(" ", strip=True)
                    m = re.search(r"(COL\$|R\$|U\$S|USD|\$)?\s*([0-9.,]+)", txt, re.I)
                    if m:
                        moneda = (m.group(1) or "").strip()
                        num = m.group(2).replace(".", "").replace(",", ".")
                        try:
                            precio = float(num)
                        except Exception:
                            precio = None

                img_el = a.select_one("img")
                img = (img_el.get("src") or img_el.get("data-src") or "") if img_el else ""

                results.append({
                    "nombre": name,
                    "url": full,
                    "tiny_image": img,
                    "precio_detectado": precio,
                    "moneda": moneda,
                })

        except Exception:
            continue

    return results


async def nuuvem_fetch_v2(product: dict) -> Optional[dict]:
    url = product.get("url")
    if not url:
        return None
    client = await get_http_client()
    headers = {"Accept-Language": "es-ES,es;q=0.9"}

    try:
        r = await client.get(url, headers=headers, timeout=15.0)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, _BS_PARSER)

        price_el = (
            soup.select_one(".product-price--val span:not(.product-price--old)")
            or soup.select_one(".product-price__price")
            or soup.select_one("[class*='product-price'] span")
            or soup.select_one("[class*='price']")
        )
        precio = None
        moneda = None
        if price_el:
            txt = price_el.get_text(" ", strip=True)
            m = re.search(r"(COL\$|R\$|U\$S|USD|\$)?\s*([0-9.,]+)", txt, re.I)
            if m:
                moneda = (m.group(1) or "").strip()
                num = m.group(2).replace(".", "").replace(",", ".")
                try:
                    precio = float(num)
                except Exception:
                    precio = None
        if precio is None:
            # Buscar cualquier número que parezca precio en la página
            for el in soup.select("[class*='price']"):
                txt = el.get_text(" ", strip=True)
                m = re.search(r"([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)", txt)
                if m:
                    try:
                        precio = float(m.group(1).replace(".", "").replace(",", "."))
                        if 0.01 < precio < 10000:
                            break
                    except Exception:
                        continue

        og = soup.find("meta", property="og:image")
        tiny = og.get("content") if og and og.get("content") else product.get("tiny_image") or ""
        name_tag = soup.find("h1") or soup.find("h2")
        nombre = name_tag.get_text(strip=True) if name_tag else product.get("nombre", "")

        return {
            "nombre": nombre,
            "precio_final": precio,
            "moneda": moneda,
            "tiny_image": tiny or "",
            "url": url,
        }
    except Exception:
        return None