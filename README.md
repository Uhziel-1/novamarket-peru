# NovaMarket Perú — E-Commerce Inteligente con Minería de Datos (CRISP-DM)

Sistema comercial web tipo marketplace multicategoría con **dos motores reales de Minería de Datos**, consumo en vivo de **APIs externas**, persistencia transaccional en **SQLite**, trazabilidad de datos (**SHA-256**) y documentación completa siguiendo las **6 fases de CRISP-DM**.

---

## 1. Qué integra el proyecto

1. **Sistema Libre (App Web POS / E-Commerce)**:
   - Catálogo navegable y **buscador inteligente** (`GET /api/products`) por texto, categoría y popularidad histórica.
   - Carrito interactivo con cálculo en vivo en **USD y PEN**, selector de perfil de cliente y emisión de boletas guardadas en SQLite (`POST /api/checkout`, `GET /api/invoices`).
   - Tablero gerencial y curvas analíticas generadas desde los datos reales.
2. **Consumo de APIs**:
   - **Externa 1 (`open.er-api.com`)**: Tipo de cambio USD → PEN en tiempo real.
   - **Externa 2 (`date.nager.at`)**: Calendario oficial de feriados de Perú (`2026/PE`) para ajustar campañas comerciales.
   - **API Propia (FastAPI)**: Endpoints `/api/recommend`, `/predict` (`/api/predict-customer`), `/api/products`, `/api/context`, `/api/checkout`, `/api/invoices` y documentación automática `/docs`.
3. **Minería de Datos (sobre 541,909 transacciones reales — UCI Online Retail)**:
   - **Motor 1 — Reglas de Asociación (Market Basket Analysis)**: `1,560` reglas extraídas de `18,532` boletas (`Confianza >= 15 %`, `Lift >= 1.5`) para recomendar *venta cruzada* en tiempo real cuando el cliente arma su carrito.
   - **Motor 2 — Segmentación RFM (`K-Means, k=4`) + Predicción de Recompra / Fuga**: Clasifica al cliente en 4 segmentos (*VIP Campeón*, *Cliente Leal*, *En Riesgo*, *Dormido / Ocasional*) y compara 3 algoritmos sin fuga temporal (*corte 2011-09-09*): `LogisticRegression` (baseline), `RandomForestClassifier` (ganador en CV-5 con `ROC-AUC = 0.7426` y `0.7647` en holdout futuro) y `HistGradientBoostingClassifier` (`0.7714` en holdout futuro), con explicabilidad **SHAP**.

---

## 2. Ejecución rápida en Windows (1 clic)

- **Abrir la aplicación web + API**: doble clic en `ABRIR_SISTEMA.bat` (abre `http://127.0.0.1:38420`, puerto raro libre para no chocar con `8000`).
- **Abrir la presentación CRISP-DM**: doble clic en `ABRIR_PRESENTACION.bat`.
- **Ejecutar pruebas automatizadas**: doble clic en `EJECUTAR_PRUEBAS.bat`.
- **Reentrenar todo el pipeline CRISP-DM desde cero**: doble clic en `REENTRENAR_MODELO.bat`.

---

## 3. Replicabilidad paso a paso (línea de comandos)

```powershell
# 1. Crear entorno virtual e instalar versiones fijadas
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2. Fase 2 y Fase 3-5 CRISP-DM (Descarga verificada SHA-256 + EDA + Entrenamiento)
.\.venv\Scripts\python.exe src\extract_data.py
.\.venv\Scripts\python.exe src\eda.py
.\.venv\Scripts\python.exe src\train.py

# 3. Verificar pruebas de contrato (FastAPI + ML + SQLite)
.\.venv\Scripts\python.exe -m pytest tests\test_api.py -v

# 4. Iniciar servidor local
.\.venv\Scripts\python.exe run_local.py
```

---

## 4. Estructura del repositorio

```text
novamarket-peru/
├── ABRIR_SISTEMA.bat          # Inicia servidor FastAPI + navegador
├── ABRIR_PRESENTACION.bat     # Abre presentación CRISP-DM exportable a PDF
├── EJECUTAR_PRUEBAS.bat       # Suite pytest de integración y validación
├── REENTRENAR_MODELO.bat      # Ejecuta extract_data + eda + train
├── requirements.txt           # Dependencias fijadas
├── run_local.py               # Arranque Uvicorn local
├── data/
│   ├── DATA_VERSION.md        # Trazabilidad y hash SHA-256 del dataset
│   ├── raw/                   # Transacciones crudas + manifiesto
│   └── processed/             # Datos limpios + matriz RFM sin fuga temporal
├── docs/                      # Documentación formal de las 6 fases CRISP-DM
├── models/                    # Pipelines .joblib, catálogo y reglas JSON
├── notebooks/                 # Notebook reproducible CRISP-DM
├── presentation/              # Diapositivas HTML/CSS/JS standalone
├── reports/                   # Métricas JSON, reglas CSV y 6 figuras PNG
├── src/                       # extract_data.py, eda.py, train.py
├── app/                       # FastAPI (main, schemas, database, external_apis, static/)
└── tests/                     # Pruebas automatizadas pytest
```
