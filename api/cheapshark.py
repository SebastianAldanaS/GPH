from typing import List, Dict, Optional
import logging

from api.http_client import get_http_client
from api.utils import _normalize_text, _similar

BASE_URL = "https://www.cheapshark.com/api/1.0"

logger = logging.getLogger(__name__)


def _title_matches_query(q_norm: str, title: str, min_similarity: float = 0.35) -> bool:
    if not q_norm or not title:
        return False
    t_norm = _normalize_text(title)
    if q_norm in t_norm:
        return True
    words = [w for w in q_norm.split() if len(w) >= 2]
    if words and sum(1 for w in words if w in t_norm) >= max(1, len(words) * 0.5):
        return True
    return _similar(q_norm, t_norm) >= min_similarity


async def cheapshark_search(q: str, limit: int = 3) -> List[Dict]:
    """Search CheapShark for the query and return matches for Fanatical (storeID == '15')."""
    client = await get_http_client()
    try:
        resp = await client.get(
            f"{BASE_URL}/games",
            params={"title": q, "limit": 20, "exact": 0},
            timeout=15.0,
        )
        resp.raise_for_status()
        juegos = resp.json() or []
    except Exception as e:
        logger.debug("CheapShark /games failed: %s", e)
        return []

    if not juegos:
        return []

    res = []
    q_norm = _normalize_text(q)

    for juego in juegos:
        if len(res) >= limit:
            break
        try:
            game_id = juego.get("gameID")
            if not game_id:
                continue
            details_resp = await client.get(f"{BASE_URL}/games", params={"id": game_id}, timeout=15.0)
            details_resp.raise_for_status()
            details = details_resp.json()

            info = details.get("info", {})
            title = info.get("title") or juego.get("external") or ""
            if not title:
                continue

            if not _title_matches_query(q_norm, title):
                continue

            deals = [d for d in details.get("deals", []) if d.get("storeID") == "15"]
            if not deals:
                continue

            best = min(deals, key=lambda d: float(d.get("price", 9999)))
            usd_price = float(best.get("price", 0.0))
            retail = best.get("retailPrice")
            retail_float = float(retail) if (retail is not None and retail != "") else None

            savings = best.get("savings")
            try:
                savings_int = int(float(savings))
            except Exception:
                savings_int = 0

            redirect = f"https://www.cheapshark.com/redirect?dealID={best.get('dealID')}"
            thumb = info.get("thumb") or ""

            res.append({
                "nombre": title,
                "precio_final": usd_price,
                "original_price": retail_float,
                "descuento": savings_int,
                "url": redirect,
                "tiny_image": thumb,
                "tienda": "Fanatical",
            })
        except Exception as e:
            logger.debug("CheapShark processing failed for juego %s: %s", juego, e)
            continue

    return res
