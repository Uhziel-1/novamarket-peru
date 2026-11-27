"""
Backend FastAPI para NovaMarket Perú:
    - Tienda Web y Buscador Inteligente con corrección aproximada (difflib + español/inglés)
    - Recomendador de Carrito y Detalle (Reglas de Asociación + Respaldo por Categoría/Popularidad)
    - Segmentación K-Means RFM + Predictor de Recompra / Fuga (RandomForest)
    - Consumo en vivo de APIs externas (Tipo de Cambio USD->PEN + Feriados Perú)
    - Analítica Gerencial con series reales históricas y boletas en SQLite
"""

from contextlib import asynccontextmanager
import difflib
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import joblib
import numpy as np
import pandas as pd

from app.database import DEFAULT_DB_PATH, init_db, insert_boleta, list_boletas
from app.external_apis import get_external_context
from app.schemas import (
    CheckoutInput,
    CustomerScoreInput,
    CustomerScoreOutput,
    RecommendInput,
)

MODELS_DIR = ROOT_DIR / "models"
REPORTS_DIR = ROOT_DIR / "reports"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
STATIC_DIR = Path(__file__).resolve().parent / "static"
FIGURES_DIR = REPORTS_DIR / "figures"

RFM_COLS = [
    "recency_days",
    "frequency",
    "monetary",
    "avg_basket_value",
    "total_items",
    "unique_products",
    "tenure_days",
    "purchase_velocity",
    "cancellation_count",
    "is_uk",
]

# Mapeo español -> términos reales del catálogo para facilitar búsquedas en Perú
ES_EN_SYNONYMS: Dict[str, str] = {
    "taza": "cup",
    "tazas": "cup",
    "te": "tea",
    "cafetera": "tea",
    "bolso": "bag",
    "bolsa": "bag",
    "bolsos": "bag",
    "mochila": "bag",
    "lonchera": "lunch",
    "corazon": "heart",
    "vela": "candle",
    "velas": "candle",
    "reloj": "clock",
    "linterna": "lantern",
    "lampara": "light",
    "luz": "light",
    "luces": "light",
    "regalo": "gift",
    "pastel": "cake",
    "torta": "cake",
    "caja": "box",
    "botella": "bottle",
    "navidad": "christmas",
    "cuaderno": "notebook",
    "libreta": "notebook",
    "lapicero": "pen",
    "plato": "plate",
    "marco": "frame",
    "fiesta": "party",
    "viaje": "travel",
}

state: Dict[str, Any] = {
    "catalog": [],
    "catalog_map": {},
    "vocab": [],
    "rules": {},
    "customers": [],
    "rfm_bundle": None,
    "churn_model": None,
    "metrics": {},
    "eda": {},
    "segment_details": [],
}


def _compute_segment_details(rfm_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    rfm_csv = PROCESSED_DIR / "rfm_customers_dataset.csv"
    if not rfm_csv.exists() or rfm_bundle is None:
        return []
    df = pd.read_csv(rfm_csv)
    rfm_log = pd.DataFrame(
        np.log1p(df[["recency_days", "frequency", "monetary"]].clip(lower=0).values),
        columns=["recency_days", "frequency", "monetary"],
    )
    df["cluster_id"] = rfm_bundle["pipeline"].predict(rfm_log)
    df["segmento"] = df["cluster_id"].map(rfm_bundle["cluster_map"])
    agg = (
        df.groupby("segmento", as_index=False)
        .agg(
            customers=("CustomerID", "count"),
            avg_monetary=("monetary", "mean"),
            total_monetary=("monetary", "sum"),
            avg_frequency=("frequency", "mean"),
            avg_recency=("recency_days", "mean"),
            repurchase_rate=("will_repurchase", "mean"),
        )
        .sort_values("avg_monetary", ascending=False)
    )
    return [
        {
            "segmento": str(r.segmento),
            "customers": int(r.customers),
            "avg_monetary": round(float(r.avg_monetary), 2),
            "total_monetary": round(float(r.total_monetary), 2),
            "avg_frequency": round(float(r.avg_frequency), 1),
            "avg_recency": round(float(r.avg_recency), 1),
            "repurchase_rate": round(float(r.repurchase_rate), 4),
        }
        for r in agg.itertuples()
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DEFAULT_DB_PATH)
    catalog = json.loads((MODELS_DIR / "catalog_products.json").read_text(encoding="utf-8"))
    state["catalog"] = catalog
    state["catalog_map"] = {p["stock_code"]: p for p in catalog}

    vocab = set()
    for p in catalog:
        for w in p["description"].lower().split():
            clean_w = "".join(ch for ch in w if ch.isalnum())
            if len(clean_w) >= 3:
                vocab.add(clean_w)
    state["vocab"] = sorted(vocab)

    state["rules"] = json.loads((MODELS_DIR / "basket_rules.json").read_text(encoding="utf-8"))
    state["customers"] = json.loads((MODELS_DIR / "sample_customers.json").read_text(encoding="utf-8"))
    state["rfm_bundle"] = joblib.load(MODELS_DIR / "modelo_segmentacion_rfm.joblib")
    state["churn_model"] = joblib.load(MODELS_DIR / "modelo_recompra_clientes.joblib")
    if (REPORTS_DIR / "metrics_summary.json").exists():
        state["metrics"] = json.loads((REPORTS_DIR / "metrics_summary.json").read_text(encoding="utf-8"))
    if (REPORTS_DIR / "eda_summary.json").exists():
        state["eda"] = json.loads((REPORTS_DIR / "eda_summary.json").read_text(encoding="utf-8"))
    state["segment_details"] = _compute_segment_details(state["rfm_bundle"])
    yield
    state["churn_model"] = None


app = FastAPI(
    title="NovaMarket Perú — E-Commerce Inteligente (CRISP-DM)",
    description=(
        "Sistema comercial con Buscador Inteligente + Corrección Aproximada, Recomendador de Carrito "
        "(Reglas de Asociación + Respaldo Comercial), Segmentación RFM K-Means, Predictor de Recompra/Fuga "
        "y APIs externas en vivo (FX + Feriados)."
    ),
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
if FIGURES_DIR.exists():
    app.mount("/figures", StaticFiles(directory=str(FIGURES_DIR)), name="figures")


@app.get("/", include_in_schema=False)
def index():
    idx = STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return {"status": "NovaMarket Perú API operativa. Visita /docs"}


@app.get("/health", tags=["Sistema"])
def health():
    return {
        "status": "ok" if state["churn_model"] is not None else "degraded",
        "productos_catalogo": len(state["catalog"]),
        "reglas_productos": len(state["rules"]),
        "bd_sqlite": DEFAULT_DB_PATH.exists(),
        "algoritmo_recompra": state["metrics"].get("winner_model", "RandomForestClassifier"),
    }


@app.get("/api/context", tags=["APIs Externas y Contexto"])
def api_context():
    """Devuelve tipo de cambio USD->PEN en vivo, feriados Perú, inventario y analítica gerencial real."""
    ext = get_external_context()
    categories = sorted({p["category"] for p in state["catalog"]})
    cat_counts: Dict[str, int] = {}
    for p in state["catalog"]:
        cat_counts[p["category"]] = cat_counts.get(p["category"], 0) + 1

    return {
        "external": ext,
        "categories": categories,
        "category_counts": cat_counts,
        "catalog_summary": {
            "active_skus": len(state["catalog"]),
            "total_units_sold": sum(int(p.get("units_sold", 0)) for p in state["catalog"]),
            "avg_price_usd": round(
                sum(float(p["price_usd"]) for p in state["catalog"]) / max(1, len(state["catalog"])),
                2,
            ),
        },
        "sample_customers": state["customers"],
        "metrics": state["metrics"],
        "eda": state["eda"],
        "segment_details": state["segment_details"],
    }


@app.get("/api/products", tags=["Tienda y Buscador Inteligente"])
def search_products(
    q: str = Query(default="", description="Búsqueda inteligente (soporta errores de tipeo y términos en español)"),
    category: str = Query(default="", description="Filtro opcional de categoría"),
    limit: int = Query(default=28, ge=1, le=150),
):
    """
    Buscador de tienda real:
    1) Traduce palabras comunes español->inglés ('taza'->'cup')
    2) Puntúa coincidencia textual exacta + popularidad en boletas históricas
    3) Si hay error de tipeo ('tecup'), detecta cercanía con difflib y sugiere corrección
    4) Siempre incluye fallback_products (más vendidos) para nunca dejar la vitrina vacía.
    """
    raw_terms = [t.strip().lower() for t in q.split() if t.strip()]
    items = state["catalog"]
    if category:
        items = [p for p in items if p["category"] == category]

    fallback_top = sorted(items, key=lambda x: x["invoice_count"], reverse=True)[:8]

    if not raw_terms:
        ordered = sorted(items, key=lambda x: x["invoice_count"], reverse=True)
        return {
            "total": len(ordered),
            "match_mode": "catalogo_popular",
            "suggestion": None,
            "products": ordered[:limit],
            "fallback_products": fallback_top,
        }

    # Expandir con sinónimo ES->EN si aplica
    expanded_terms: List[str] = []
    mapped_notes: List[str] = []
    for t in raw_terms:
        if t in ES_EN_SYNONYMS:
            en_w = ES_EN_SYNONYMS[t]
            expanded_terms.append(en_w)
            mapped_notes.append(f"{t} → {en_w}")
        expanded_terms.append(t)

    # Paso 1: Coincidencia exacta/subcadena
    scored = []
    for p in items:
        desc_low = p["description"].lower()
        code_low = p["stock_code"].lower()
        cat_low = p["category"].lower()
        hits = sum(1 for t in expanded_terms if t in desc_low or t in code_low or t in cat_low)
        if hits > 0:
            score = hits * 100.0 + (25.0 if any(desc_low.startswith(t) for t in expanded_terms) else 0.0) + np.log1p(p["invoice_count"])
            scored.append((score, p))

    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        return {
            "total": len(scored),
            "match_mode": "sinonimo_es" if mapped_notes else "exacto",
            "suggestion": ", ".join(mapped_notes) if mapped_notes else None,
            "products": [p for _, p in scored[:limit]],
            "fallback_products": fallback_top,
        }

    # Paso 2: Corrección aproximada (fuzzy) sobre el vocabulario real del catálogo
    fuzzy_words: List[str] = []
    for t in raw_terms:
        close = difflib.get_close_matches(t, state["vocab"], n=3, cutoff=0.60)
        fuzzy_words.extend(close)

    fuzzy_scored = []
    if fuzzy_words:
        for p in items:
            desc_low = p["description"].lower()
            hits = sum(1 for fw in fuzzy_words if fw in desc_low)
            if hits > 0:
                score = hits * 80.0 + np.log1p(p["invoice_count"])
                fuzzy_scored.append((score, p))

    if fuzzy_scored:
        fuzzy_scored.sort(key=lambda x: x[0], reverse=True)
        return {
            "total": len(fuzzy_scored),
            "match_mode": "aproximado",
            "suggestion": fuzzy_words[0],
            "products": [p for _, p in fuzzy_scored[:limit]],
            "fallback_products": fallback_top,
        }

    # Paso 3: Sin coincidencia -> devolver productos promocionados de la categoría/tienda
    return {
        "total": 0,
        "match_mode": "promocion_alternativa",
        "suggestion": None,
        "products": [],
        "fallback_products": fallback_top,
    }


@app.post("/api/recommend", tags=["Minería de Datos: Reglas de Asociación"])
def recommend_for_cart(payload: RecommendInput):
    """
    Recomienda primero productos conectados por Reglas de Asociación (Confianza + Lift).
    Si no alcanzan para llenar 'limit' (o el producto no tiene reglas fuertes), completa con
    artículos complementarios de la misma categoría y más vendidos para nunca dejar de promocionar.
    """
    cart_set = set(payload.cart_codes)
    recs: List[Dict[str, Any]] = []
    seen_codes = set(cart_set)

    if cart_set:
        aggregated: Dict[str, Dict[str, Any]] = {}
        for code in cart_set:
            for r in state["rules"].get(code, []):
                target = r["consequent"]
                if target in seen_codes:
                    continue
                score = r["lift"] * r["confidence"]
                if target not in aggregated or score > aggregated[target]["_score"]:
                    aggregated[target] = {
                        **r,
                        "_score": score,
                        "based_on": r["antecedent_name"],
                        "match_type": "regla_asociacion",
                    }
        ranked = sorted(aggregated.values(), key=lambda x: x["_score"], reverse=True)[: payload.limit]
        for r in ranked:
            r.pop("_score", None)
            seen_codes.add(r["consequent"])
            recs.append(r)

    # Completar hasta payload.limit promocionando misma categoría y luego más vendidos
    if len(recs) < payload.limit:
        cart_cats = {
            state["catalog_map"][c]["category"]
            for c in cart_set
            if c in state["catalog_map"]
        }
        same_cat = [
            p for p in state["catalog"]
            if p["stock_code"] not in seen_codes and p["category"] in cart_cats
        ]
        other_top = [
            p for p in state["catalog"]
            if p["stock_code"] not in seen_codes and p["category"] not in cart_cats
        ]
        for source_list, mtype, reason in [
            (same_cat, "complemento_categoria", "Complemento popular de la misma categoría"),
            (other_top, "promocion_tienda", "Más vendido de la tienda"),
        ]:
            for p in source_list:
                if len(recs) >= payload.limit:
                    break
                seen_codes.add(p["stock_code"])
                recs.append(
                    {
                        "consequent": p["stock_code"],
                        "consequent_name": p["description"],
                        "consequent_category": p["category"],
                        "consequent_price_usd": p["price_usd"],
                        "co_purchases": p["invoice_count"],
                        "support": None,
                        "confidence": None,
                        "lift": None,
                        "based_on": reason,
                        "match_type": mtype,
                    }
                )

    has_rules = any(r.get("match_type") == "regla_asociacion" for r in recs)
    mode = "reglas_asociacion" if has_rules else "popularidad"
    return {"mode": mode, "recommendations": recs[: payload.limit]}


@app.post("/predict", response_model=CustomerScoreOutput, tags=["Minería de Datos: RFM y Recompra"])
@app.post("/api/predict-customer", response_model=CustomerScoreOutput, tags=["Minería de Datos: RFM y Recompra"])
def predict_customer(payload: CustomerScoreInput):
    """Asigna segmento RFM (K-Means) y predice probabilidad de recompra en el próximo trimestre."""
    model = state["churn_model"]
    rfm_bundle = state["rfm_bundle"]
    if model is None or rfm_bundle is None:
        raise HTTPException(status_code=503, detail="Modelos no inicializados")

    t0 = time.perf_counter()
    avg_basket = payload.avg_basket_value or round(payload.monetary / payload.frequency, 2)
    velocity = payload.purchase_velocity if payload.purchase_velocity is not None else round(
        payload.frequency / ((payload.tenure_days / 30.0) + 1.0), 3
    )

    # 1. Segmento K-Means RFM (DataFrame con nombres para evitar warnings de sklearn)
    rfm_df = pd.DataFrame(
        np.log1p([[payload.recency_days, payload.frequency, payload.monetary]]),
        columns=["recency_days", "frequency", "monetary"],
    )
    cid = int(rfm_bundle["pipeline"].predict(rfm_df)[0])
    segmento = rfm_bundle["cluster_map"][cid]

    # 2. Probabilidad supervisada de Recompra
    row = {
        "recency_days": payload.recency_days,
        "frequency": payload.frequency,
        "monetary": payload.monetary,
        "avg_basket_value": avg_basket,
        "total_items": payload.total_items,
        "unique_products": payload.unique_products,
        "tenure_days": payload.tenure_days,
        "purchase_velocity": velocity,
        "cancellation_count": payload.cancellation_count,
        "is_uk": payload.is_uk,
    }
    X_row = pd.DataFrame([row])[RFM_COLS]
    p_recompra = float(model.predict_proba(X_row)[0, 1])
    p_fuga = 1.0 - p_recompra
    pred = int(p_recompra >= 0.5)

    factores: List[str] = []
    if payload.recency_days <= 30:
        factores.append(f"Compra reciente ({payload.recency_days} días desde última visita)")
    elif payload.recency_days >= 90:
        factores.append(f"Inactividad prolongada ({payload.recency_days} días sin comprar)")
    if payload.frequency >= 6:
        factores.append(f"Alta recurrencia ({payload.frequency} boletas históricas)")
    elif payload.frequency <= 2:
        factores.append(f"Baja frecuencia histórica ({payload.frequency} compras)")
    if payload.monetary >= 1500:
        factores.append(f"Alto valor acumulado (${payload.monetary:,.0f} USD)")
    if payload.tenure_days >= 120:
        factores.append(f"Relación madura ({payload.tenure_days} días de antigüedad)")
    if payload.cancellation_count > 0:
        factores.append(f"Registra {payload.cancellation_count} cancelación(es) previa(s)")

    if p_recompra >= 0.70:
        nivel = "Alta Fidelidad"
        accion = "Ofrecer venta cruzada premium o envío prioritario sin necesidad de descuento agresivo."
    elif p_recompra >= 0.45:
        nivel = "Estable / Seguimiento"
        accion = "Activar recomendaciones del carrito y recordar catálogo nuevo en campaña."
    else:
        nivel = "Riesgo de Fuga"
        accion = "ALERTA DE RETENCIÓN: entregar cupón de 10 %–15 % en caja para incentivar próxima compra."

    ms = round((time.perf_counter() - t0) * 1000, 2)
    return CustomerScoreOutput(
        customer_id=payload.customer_id,
        segmento_rfm=segmento,
        probabilidad_recompra=round(p_recompra, 4),
        probabilidad_fuga=round(p_fuga, 4),
        prediccion_recompra=pred,
        nivel_retencion=nivel,
        factores_clave=factores[:4] or ["Perfil estándar dentro de la cartera"],
        accion_comercial=accion,
        tiempo_inferencia_ms=ms,
    )


@app.get("/api/invoices", tags=["Persistencia SQLite"])
def get_invoices():
    rows = list_boletas(limit=30, db_path=DEFAULT_DB_PATH)
    total_pen = round(sum(r["total_pen"] for r in rows), 2)
    total_usd = round(sum(r["total_usd"] for r in rows), 2)
    rec_used = sum(1 for r in rows if r["used_recommendation"])
    return {
        "count": len(rows),
        "total_usd": total_usd,
        "total_pen": total_pen,
        "with_recommendation": rec_used,
        "invoices": rows,
    }


@app.post("/api/checkout", status_code=status.HTTP_201_CREATED, tags=["Persistencia SQLite"])
def checkout(payload: CheckoutInput):
    ext = get_external_context()
    rate = float(ext["usd_to_pen"])
    total_usd = sum(it.quantity * it.price_usd for it in payload.items)
    total_pen = total_usd * rate
    created = insert_boleta(
        customer_id=payload.customer_id,
        segmento=payload.segmento,
        items=[it.model_dump() for it in payload.items],
        total_usd=total_usd,
        total_pen=total_pen,
        exchange_rate=rate,
        used_recommendation=payload.used_recommendation,
        db_path=DEFAULT_DB_PATH,
    )
    return created
