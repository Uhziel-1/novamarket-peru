# Fase 6 CRISP-DM — Despliegue del Sistema Web, APIs y Pruebas

> **Backend & Web App:** `app/main.py`, `app/database.py`, `app/external_apis.py`, `app/schemas.py`, `app/static/`  
> **Pruebas automatizadas:** `tests/test_api.py` (`5 passed`)

---

## 1. Contrato de Endpoints FastAPI

| Método y Ruta | Función | Tecnología Involucrada |
| :--- | :--- | :--- |
| `GET /` | Interfaz web interactiva (`NovaMarket Perú`) | HTML + CSS + JavaScript + `Chart.js` |
| `GET /health` | Diagnóstico del servicio, catálogo, reglas y SQLite | FastAPI Lifespan |
| `GET /api/context` | Contexto comercial + **APIs externas en vivo** + métricas CRISP-DM | `open.er-api.com` (`USD -> PEN`) + `date.nager.at` (`Feriados PE`) |
| `GET /api/products` | Buscador inteligente por texto, categoría y popularidad | Ranking textual + popularidad en `18,532` boletas |
| `POST /api/recommend` | Recomendaciones de venta cruzada para el carrito actual | `1,560` Reglas de Asociación (`Confianza`, `Lift`) |
| `POST /predict` (`y /api/predict-customer`) | Segmento RFM (`K-Means`) + Probabilidad de Recompra/Fuga + acción | `StandardScaler + KMeans` + `RandomForestClassifier` |
| `POST /api/checkout` & `GET /api/invoices` | Registro y consulta de boletas bimoneda (`USD` y `PEN`) | Persistencia en `SQLite` (`data/novamarket.db`) |

---

## 2. Verificación Funcional y Contrato

- **Pruebas automatizadas (`pytest tests/test_api.py -v`):** `5/5` casos aprobados con base SQLite temporal aislada (`tmp_path`), verificando:
  1. Salud del servicio y carga de modelos (`>= 100` productos, `>= 50` códigos con reglas).
  2. Contexto externo (tipo de cambio `USD -> PEN` real) y buscador de catálogo.
  3. Recomendador de asociación con producto `22698` (`Confianza > 0.15`, `Lift >= 1.5`) y fallback sin carrito.
  4. Scoring `/predict` válido + rechazo HTTP `422` ante entrada inválida (`frequency=0`).
  5. Emisión de boleta (`201 Created`) y consulta persistida en SQLite.
- **Operación en 1 clic:** `ABRIR_SISTEMA.bat` levanta Uvicorn (Web + API en el mismo puerto) en `http://127.0.0.1:38420` y abre el navegador automáticamente.
