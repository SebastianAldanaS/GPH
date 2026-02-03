from typing import List
from http_client import get_http_client

STORE_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STORE_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"


async def store_search(query: str, cc: str = "co", limit: int = 5) -> List[dict]:
    client = await get_http_client()
    params = {"term": query, "cc": cc, "l": "en"}
    try:
        resp = await client.get(STORE_SEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        exclude_keywords = ("soundtrack", "soundtracks", "demo", "demos", "extra", "extras")
        filtered = [item for item in items if not any(kw in item.get("name", "").lower() for kw in exclude_keywords)]
        return filtered[:limit]
    except Exception as e:
        raise RuntimeError(f"Error searching Steam store: {e}")


async def fetch_price_for_app(appid: int, cc: str = "co") -> dict:
    client = await get_http_client()
    params = {"appids": str(appid), "cc": cc, "l": "en"}
    try:
        resp = await client.get(STORE_APPDETAILS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        appdata = data.get(str(appid), {})
        if not appdata.get("success"):
            raise RuntimeError("Steam store did not return success for this appid")
        return appdata.get("data", {})
    except Exception as e:
        raise RuntimeError(f"Error fetching Steam store data: {e}")