from fastapi import APIRouter, HTTPException, Query
from typing import List
from api.schemas import Suggestion, Preview, GamePrice
from api.steam import store_search, fetch_price_for_app
from api.nuuvem import nuuvem_search_v2, nuuvem_fetch_v2
from api.cheapshark import cheapshark_search
from api.greenmangaming import gmg_search
from api.instantgaming import instantgaming_search
from api.utils import _normalize_text
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health():
    """Para comprobaciones de Railway / monitoreo."""
    return {"status": "ok"}


@router.get("/autocomplete", response_model=List[Suggestion])
async def autocomplete(q: str = Query(..., min_length=1), limit: int = Query(8, ge=1, le=20), cc: str = Query("co", min_length=2, max_length=2)):
    try:
        items = await store_search(q, cc, limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    suggestions = [Suggestion(appid=item.get("id"), nombre=item.get("name"), tiny_image=item.get("tiny_image")) for item in items]
    return suggestions


@router.get("/preview", response_model=Preview)
async def preview(appid: int = Query(...), cc: str = Query("co", min_length=2, max_length=2)):
    try:
        data = await fetch_price_for_app(appid, cc)
    except Exception:
        raise HTTPException(status_code=404, detail="No se encontró información para este appid")

    if data.get("is_free"):
        image = data.get("header_image") or data.get("capsule_image") or f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/capsule_184x69.jpg"
        return Preview(
            appid=appid,
            nombre=data.get("name", ""),
            precio_final=0.0,
            precio_original=None,
            porcentaje_descuento=0,
            moneda=data.get("currency", "COP"),
            is_free=True,
            steam_url=f"https://store.steampowered.com/app/{appid}/",
            tiny_image=image,
        )

    price = data.get("price_overview")
    if not price:
        raise HTTPException(status_code=404, detail="No hay información de precio")

    final = price.get("final", 0) / 100
    initial = price.get("initial", 0) / 100
    discount = price.get("discount_percent", 0)

    image = data.get("header_image") or data.get("capsule_image") or f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/capsule_184x69.jpg"
    return Preview(
        appid=appid,
        nombre=data.get("name", ""),
        precio_final=round(final, 2),
        precio_original=round(initial, 2) if initial != final else None,
        porcentaje_descuento=discount,
        moneda=price.get("currency"),
        is_free=False,
        steam_url=f"https://store.steampowered.com/app/{appid}/",
        tiny_image=image,
    )


@router.get('/search', response_model=List[GamePrice])
async def search(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20), cc: str = Query('co', min_length=2, max_length=2)):
    try:
        items = await store_search(q, cc, limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    results = []

    # If Steam search didn't return items, try Instant Gaming as a fallback
    if not items:
        try:
            ig_candidates = await instantgaming_search(q, limit)
        except Exception:
            ig_candidates = []

        for cand in ig_candidates:
            if not cand or not cand.get('precio'):
                continue

            results.append(GamePrice(
                appid=0,
                nombre=cand.get('nombre') or q,
                precio_final=round(cand.get('precio') or 0.0, 2),
                precio_original=round(cand.get('precio_original'), 2) if cand.get('precio_original') else None,
                porcentaje_descuento=int(cand.get('porcentaje_descuento', 0) or 0),
                moneda=cand.get('moneda') or 'EUR',
                steam_url=cand.get('url'),
                tiny_image=cand.get('tiny_image') or ''
            ))

        if results:
            return results

        raise HTTPException(status_code=404, detail="No se encontraron coincidencias")

    results = []
    for item in items:
        appid = item.get("id")
        name = item.get("name")
        try:
            store_data = await fetch_price_for_app(appid, cc)
        except Exception:
            store_data = {}

        if store_data.get("is_free"):
            image = item.get("tiny_image") or store_data.get("header_image") or store_data.get("capsule_image") or f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/capsule_184x69.jpg"
            results.append(GamePrice(
                appid=appid,
                nombre=name,
                precio_final=0.0,
                precio_original=None,
                porcentaje_descuento=0,
                moneda=store_data.get("currency", item.get("price", {}).get("currency", "COP")),
                steam_url=f"https://store.steampowered.com/app/{appid}/",
                tiny_image=image,
            ))
            continue

        price = store_data.get("price_overview") or item.get("price")
        if not price:
            continue

        final = price.get("final", 0) / 100
        initial = price.get("initial", 0) / 100
        discount = price.get("discount_percent", 0)

        image = item.get("tiny_image") or store_data.get("header_image") or store_data.get("capsule_image") or f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/capsule_184x69.jpg"
        results.append(GamePrice(
            appid=appid,
            nombre=name,
            precio_final=round(final, 2),
            precio_original=round(initial, 2) if initial != final else None,
            porcentaje_descuento=discount,
            moneda=price.get("currency"),
            steam_url=f"https://store.steampowered.com/app/{appid}/",
            tiny_image=image,
        ))

    # Merge Instant Gaming results into the final result set (deduplicate by normalized title)
    try:
        ig_candidates = await instantgaming_search(q, limit)
    except Exception as e:
        ig_candidates = []
        logger.debug('instantgaming_search failed while merging: %s', e)

    if ig_candidates:
        logger.debug('Merging Instant Gaming candidates (%s) into search results for query=%s', len(ig_candidates), q)
        existing_norm = set(_normalize_text(r.nombre) for r in results if getattr(r, 'nombre', None))
        for cand in ig_candidates:
            if not cand or not cand.get('precio'):
                continue
            n = _normalize_text(cand.get('nombre') or '')
            if n in existing_norm:
                continue
            results.append(GamePrice(
                appid=0,
                nombre=cand.get('nombre') or q,
                precio_final=round(cand.get('precio') or 0.0, 2),
                precio_original=round(cand.get('precio_original'), 2) if cand.get('precio_original') else None,
                porcentaje_descuento=int(cand.get('porcentaje_descuento', 0) or 0),
                moneda=cand.get('moneda') or 'EUR',
                steam_url=cand.get('url'),
                tiny_image=cand.get('tiny_image') or ''
            ))
            existing_norm.add(n)

    # Enforce client-requested limit on combined results
    if len(results) > limit:
        results = results[:limit]

    if not results:
        raise HTTPException(status_code=404, detail="No se encontró información de precios para las coincidencias")

    return results


@router.get('/nuuvem', response_model=List[GamePrice])
async def nuuvem(q: str = Query(..., min_length=1), limit: int = Query(3, ge=1, le=10), cc: str = Query('co', min_length=2, max_length=2)):
    key = f"{q}:{cc}:{limit}"
    # caching is handled inside nuuvem module if desired; keep lightweight here
    candidates = await nuuvem_search_v2(q, limit)
    results = []

    for cand in candidates:
        info = None
        if cand.get('precio_detectado'):
            info = {
                'nombre': cand.get('nombre'),
                'precio_final': cand.get('precio_detectado'),
                'precio_original': None,
                'porcentaje_descuento': 0,
                'moneda': cand.get('moneda'),
                'tiny_image': cand.get('tiny_image') or '',
                'url': cand.get('url')
            }
        else:
            info = await nuuvem_fetch_v2(cand)

        if not info or not info.get('precio_final'):
            continue

        results.append(GamePrice(
            appid=0,
            nombre=info.get('nombre') or cand.get('nombre') or q,
            precio_final=round(info.get('precio_final') or 0.0, 2),
            precio_original=round(info.get('precio_original'), 2) if info.get('precio_original') else None,
            porcentaje_descuento=info.get('porcentaje_descuento', 0),
            moneda=info.get('moneda') or 'COP',
            steam_url=info.get('url'),
            tiny_image=info.get('tiny_image') or ''
        ))

    if not results:
        raise HTTPException(status_code=502, detail='No se pudo obtener información de Nuuvem para esa búsqueda')

    return results


@router.get('/fanatical', response_model=List[GamePrice])
async def fanatical(q: str = Query(..., min_length=1), limit: int = Query(3, ge=1, le=10), cc: str = Query('co', min_length=2, max_length=2)):
    # CheapShark (Fanatical) search
    candidates = await cheapshark_search(q, limit)
    results = []

    for cand in candidates:
        if not cand or not cand.get('precio_final'):
            continue

        results.append(GamePrice(
            appid=0,
            nombre=cand.get('nombre') or q,
            precio_final=round(cand.get('precio_final') or 0.0, 2),
            precio_original=round(cand.get('original_price'), 2) if cand.get('original_price') else None,
            porcentaje_descuento=int(cand.get('descuento', 0) or 0),
            moneda='USD',
            steam_url=cand.get('url'),
            tiny_image=cand.get('tiny_image') or ''
        ))

    if not results:        # No valid price results from Steam items — try Instant Gaming as fallback
        try:
            ig_candidates = await instantgaming_search(q, limit)
        except Exception as e:
            ig_candidates = []
            logger.debug('instantgaming_search failed during fallback: %s', e)

        if ig_candidates:
            logger.debug('Fallback: Instant Gaming returned %s candidates for query=%s', len(ig_candidates), q)
            for cand in ig_candidates:
                if not cand or not cand.get('precio'):
                    continue

                results.append(GamePrice(
                    appid=0,
                    nombre=cand.get('nombre') or q,
                    precio_final=round(cand.get('precio') or 0.0, 2),
                    precio_original=round(cand.get('precio_original'), 2) if cand.get('precio_original') else None,
                    porcentaje_descuento=int(cand.get('porcentaje_descuento', 0) or 0),
                    moneda=cand.get('moneda') or 'EUR',
                    steam_url=cand.get('url'),
                    tiny_image=cand.get('tiny_image') or ''
                ))

            return results
        raise HTTPException(status_code=404, detail='No se encontraron coincidencias en Fanatical')

    return results


@router.get('/greenmangaming', response_model=List[GamePrice])
async def greenmangaming(q: str = Query(..., min_length=1), limit: int = Query(3, ge=1, le=10), cc: str = Query('co', min_length=2, max_length=2)):
    print('DEBUG: greenmangaming request q=%s limit=%s cc=%s' % (q, limit, cc))
    try:
        candidates = await gmg_search(q, limit)
        print('DEBUG: gmg_search returned %s candidates' % len(candidates))
    except Exception as e:
        print('DEBUG: gmg_search failed', e)
        raise HTTPException(status_code=502, detail='Error al consultar GreenManGaming')

    results = []

    for cand in candidates:
        logger.debug('candidate: %s', cand)
        if not cand or not cand.get('precio'):
            continue

        moneda = cand.get('moneda') or 'USD'
        results.append(GamePrice(
            appid=0,
            nombre=cand.get('nombre') or q,
            precio_final=round(cand.get('precio') or 0.0, 2),
            precio_original=round(cand.get('precio_original'), 2) if cand.get('precio_original') else None,
            porcentaje_descuento=int(cand.get('porcentaje_descuento', 0) or 0),
            moneda=moneda,
            steam_url=cand.get('url'),
            tiny_image=cand.get('tiny_image') or ''
        ))

    if not results:
        raise HTTPException(status_code=404, detail='No se encontraron coincidencias en GreenManGaming')

    return results

@router.get('/greenmangaming/debug')
async def greenmangaming_debug(q: str = Query(..., min_length=1), limit: int = Query(3, ge=1, le=10)):
    """Debug: return raw candidates from gmg_search"""
    try:
        candidates = await gmg_search(q, limit)
        return candidates
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get('/instantgaming', response_model=List[GamePrice])
async def instantgaming(q: str = Query(..., min_length=1), limit: int = Query(3, ge=1, le=10), cc: str = Query('co', min_length=2, max_length=2)):
    try:
        candidates = await instantgaming_search(q, limit)
    except Exception as e:
        print('DEBUG: instantgaming_search failed', e)
        raise HTTPException(status_code=502, detail='Error al consultar Instant Gaming')

    results = []

    for cand in candidates:
        if not cand or not cand.get('precio'):
            continue

        results.append(GamePrice(
            appid=0,
            nombre=cand.get('nombre') or q,
            precio_final=round(cand.get('precio') or 0.0, 2),
            precio_original=round(cand.get('precio_original'), 2) if cand.get('precio_original') else None,
            porcentaje_descuento=int(cand.get('porcentaje_descuento', 0) or 0),
            moneda=cand.get('moneda') or 'EUR',
            steam_url=cand.get('url'),
            tiny_image=cand.get('tiny_image') or ''
        ))

    if not results:
        raise HTTPException(status_code=404, detail='No se encontraron coincidencias en Instant Gaming')

    return results


@router.get('/instantgaming/debug')
async def instantgaming_debug(q: str = Query(..., min_length=1), limit: int = Query(3, ge=1, le=10)):
    """Debug: return raw candidates from instantgaming_search"""
    try:
        candidates = await instantgaming_search(q, limit)
        return candidates
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))