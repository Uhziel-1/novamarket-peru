"""
Pruebas automatizadas de integración y contrato para NovaMarket Perú (FastAPI + ML + SQLite).
"""

import pytest
from fastapi.testclient import TestClient

import app.main as main_mod
from app.database import init_db


@pytest.fixture()
def client(tmp_path):
    test_db = tmp_path / "test_novamarket.db"
    init_db(test_db)
    original_db = main_mod.DEFAULT_DB_PATH
    main_mod.DEFAULT_DB_PATH = test_db
    try:
        with TestClient(main_mod.app) as test_client:
            yield test_client
    finally:
        main_mod.DEFAULT_DB_PATH = original_db


def test_home_and_health(client):
    r_home = client.get("/")
    assert r_home.status_code == 200
    assert "NovaMarket" in r_home.text

    r_health = client.get("/health")
    assert r_health.status_code == 200
    body = r_health.json()
    assert body["status"] == "ok"
    assert body["productos_catalogo"] >= 100
    assert body["reglas_productos"] >= 50
    assert body["bd_sqlite"] is True


def test_api_context_and_products(client):
    r_ctx = client.get("/api/context")
    assert r_ctx.status_code == 200
    ctx = r_ctx.json()
    assert "external" in ctx
    assert ctx["external"]["usd_to_pen"] > 1.0
    assert len(ctx["categories"]) >= 3
    assert len(ctx["sample_customers"]) >= 4
    assert len(ctx["eda"]["monthly_series"]) >= 12
    assert len(ctx["segment_details"]) == 4

    r_prod = client.get("/api/products?q=teacup&limit=5")
    assert r_prod.status_code == 200
    pdata = r_prod.json()
    assert pdata["total"] >= 1
    assert pdata["match_mode"] == "exacto"

    # Corrección aproximada ante error de tipeo + sinónimo español
    r_fuzzy = client.get("/api/products?q=tecup&limit=5")
    assert r_fuzzy.status_code == 200
    assert r_fuzzy.json()["match_mode"] == "aproximado"
    assert r_fuzzy.json()["suggestion"] == "teacup"

    r_es = client.get("/api/products?q=taza&limit=5")
    assert r_es.status_code == 200
    assert r_es.json()["match_mode"] == "sinonimo_es"
    assert r_es.json()["total"] >= 1


def test_association_rules_recommendation(client):
    # Producto estrella con reglas fuertes verificadas: 22698 (Pink Regency Teacup And Saucer)
    r_rec = client.post("/api/recommend", json={"cart_codes": ["22698"], "limit": 4})
    assert r_rec.status_code == 200
    data = r_rec.json()
    assert data["mode"] == "reglas_asociacion"
    assert len(data["recommendations"]) == 4
    first = data["recommendations"][0]
    assert "22698" != first["consequent"]
    assert first["confidence"] > 0.15
    assert first["lift"] >= 1.5

    # Producto con pocas reglas fuertes: completa hasta limit=4 con categoría/top ventas
    r_backfill = client.post("/api/recommend", json={"cart_codes": ["85123A"], "limit": 4})
    assert r_backfill.status_code == 200
    assert len(r_backfill.json()["recommendations"]) == 4

    # Sin carrito: fallback por popularidad
    r_empty = client.post("/api/recommend", json={"cart_codes": [], "limit": 3})
    assert r_empty.status_code == 200
    assert r_empty.json()["mode"] == "popularidad"


def test_predict_customer_scoring_and_validation(client):
    payload = {
        "customer_id": 14646,
        "recency_days": 10,
        "frequency": 20,
        "monetary": 8500.0,
        "total_items": 1500,
        "unique_products": 120,
        "tenure_days": 250,
        "cancellation_count": 0,
        "is_uk": "Internacional",
    }
    r = client.post("/predict", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert 0.0 <= res["probabilidad_recompra"] <= 1.0
    assert 0.0 <= res["probabilidad_fuga"] <= 1.0
    assert abs((res["probabilidad_recompra"] + res["probabilidad_fuga"]) - 1.0) < 0.01
    assert res["segmento_rfm"] in {
        "VIP Campeón",
        "Cliente Leal",
        "En Riesgo",
        "Dormido / Ocasional",
    }
    assert len(res["factores_clave"]) >= 1

    # Validación Pydantic: frequency=0 debe devolver 422
    bad_payload = {**payload, "frequency": 0}
    r_bad = client.post("/predict", json=bad_payload)
    assert r_bad.status_code == 422


def test_checkout_and_invoices_sqlite(client):
    checkout_payload = {
        "customer_id": 14646,
        "segmento": "VIP Campeón",
        "used_recommendation": True,
        "items": [
            {
                "stock_code": "22698",
                "description": "Pink Regency Teacup And Saucer",
                "quantity": 2,
                "price_usd": 2.95,
            }
        ],
    }
    r_post = client.post("/api/checkout", json=checkout_payload)
    assert r_post.status_code == 201
    created = r_post.json()
    assert created["customer_id"] == 14646
    assert created["used_recommendation"] is True
    assert created["total_usd"] == pytest.approx(5.9, rel=1e-2)

    r_list = client.get("/api/invoices")
    assert r_list.status_code == 200
    inv = r_list.json()
    assert inv["count"] == 1
    assert inv["with_recommendation"] == 1
