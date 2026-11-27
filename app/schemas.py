"""
Esquemas Pydantic v2 para la API de NovaMarket Perú.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RecommendInput(BaseModel):
    cart_codes: List[str] = Field(default_factory=list, description="Códigos StockCode en el carrito")
    limit: int = Field(default=4, ge=1, le=10)


class CustomerScoreInput(BaseModel):
    customer_id: Optional[int] = Field(default=None, description="ID referencial del cliente")
    recency_days: int = Field(..., ge=0, le=500, description="Días desde la última compra")
    frequency: int = Field(..., ge=1, le=500, description="Número total de boletas previas")
    monetary: float = Field(..., ge=1.0, le=500000.0, description="Gasto acumulado en USD")
    avg_basket_value: Optional[float] = Field(None, ge=0.5, le=100000.0)
    total_items: int = Field(10, ge=1, le=200000)
    unique_products: int = Field(5, ge=1, le=5000)
    tenure_days: int = Field(60, ge=0, le=1000)
    purchase_velocity: Optional[float] = Field(None, ge=0.0, le=100.0)
    cancellation_count: int = Field(0, ge=0, le=200)
    is_uk: str = Field(default="Internacional", pattern="^(UK|Internacional)$")

    model_config = {
        "json_schema_extra": {
            "example": {
                "customer_id": 14646,
                "recency_days": 12,
                "frequency": 18,
                "monetary": 6450.0,
                "total_items": 1200,
                "unique_products": 95,
                "tenure_days": 240,
                "cancellation_count": 0,
                "is_uk": "Internacional",
            }
        }
    }


class CustomerScoreOutput(BaseModel):
    customer_id: Optional[int]
    segmento_rfm: str
    probabilidad_recompra: float
    probabilidad_fuga: float
    prediccion_recompra: int
    nivel_retencion: str
    factores_clave: List[str]
    accion_comercial: str
    tiempo_inferencia_ms: float


class CheckoutItem(BaseModel):
    stock_code: str
    description: str
    quantity: int = Field(..., ge=1, le=500)
    price_usd: float = Field(..., ge=0.1, le=10000.0)


class CheckoutInput(BaseModel):
    customer_id: int = Field(..., ge=1)
    segmento: str = Field(default="Cliente Leal")
    items: List[CheckoutItem] = Field(..., min_length=1)
    used_recommendation: bool = Field(default=False)
