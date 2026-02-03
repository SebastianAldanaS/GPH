from typing import Optional
from pydantic import BaseModel


class GamePrice(BaseModel):
    appid: int
    nombre: str
    precio_final: float
    precio_original: Optional[float] = None
    porcentaje_descuento: int = 0
    moneda: Optional[str] = "COP"
    steam_url: str
    tiny_image: str = ""


class Suggestion(BaseModel):
    appid: int
    nombre: str
    tiny_image: str = ""


class Preview(BaseModel):
    appid: int
    nombre: str
    precio_final: Optional[float] = None
    precio_original: Optional[float] = None
    porcentaje_descuento: int = 0
    moneda: Optional[str] = "COP"
    is_free: bool = False
    steam_url: str
    tiny_image: str = ""