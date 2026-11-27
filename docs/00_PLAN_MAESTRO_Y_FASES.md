# 00 — Plan Maestro de Desarrollo: `NovaMarket Perú` (Completado)

> **Enfoque CRISP-DM completo:** Sistema comercial **NovaMarket Perú** (E-commerce / Punto de Venta multicategoría) con dos motores reales de Minería de Datos, consumo de APIs externas en vivo, base de datos SQLite, trazabilidad SHA-256, pruebas automatizadas y presentación HTML optimizada para exportación PDF.

---

## Arquitectura Implementada

| Componente | Tecnología | Qué hace |
| :--- | :--- | :--- |
| **Dataset Base Real** | `data/raw/online_retail.csv` (541,909 filas) | Transacciones reales de comercio electrónico multicategoría (`2010-12-01` a `2011-12-09`). |
| **APIs Externas (En vivo)** | `open.er-api.com` + `date.nager.at` | Tipo de cambio real **USD → PEN** en caja + detección de **Feriados de Perú (`2026/PE`)**. |
| **Motor 1 (Market Basket)** | Reglas de Asociación (`Soporte`, `Confianza`, `Lift`) | `1,560` reglas sobre `150` productos del catálogo (`Lift >= 1.5`, `Conf >= 15 %`) para recomendación cruzada en carrito. |
| **Motor 2 (RFM + Recompra)** | `K-Means (k=4)` + `RandomForestClassifier` + `SHAP` | Segmentación de clientes y predicción de recompra a 90 días sin fuga temporal (`Holdout ROC-AUC = 0.7647`, `PR-AUC = 0.8295`). |
| **Sistema Libre (Web + BD)** | `FastAPI` + `SQLite` + `Chart.js` | Tienda web con buscador inteligente, carrito en USD/PEN, selector de perfiles, boletas persistentes y dashboard. |
| **Reproducibilidad y Entrega** | `.venv`, `requirements.txt`, `pytest`, `.bat`, PPT HTML | 5 pruebas `pytest` aprobadas, scripts `.bat` de 1 clic y presentación standalone exportable a PDF (`Ctrl + P`). |

---

## Estado de Fases CRISP-DM

- [x] **Fase 0 — Entorno y Extracción Inicial:** `.venv` (Python 3.12.8), descarga verificada (`SHA-256: a2f79bbdd4463df6db8a3f5a50b9c980ae8f645a370bf5e2c0d6097f9e817b05`) y APIs externas verificadas `200 OK`.
- [x] **Fase 1 — Comprensión del Negocio:** [01_FASE1_Comprension_Negocio.md](./01_FASE1_Comprension_Negocio.md).
- [x] **Fase 2 — Comprensión de los Datos (EDA):** [02_FASE2_Comprension_Datos_EDA.md](./02_FASE2_Comprension_Datos_EDA.md) + `src/eda.py` + figuras `01`–`03`.
- [x] **Fase 3 — Preparación de Datos e Ingeniería:** [03_FASE3_Preparacion_Datos.md](./03_FASE3_Preparacion_Datos.md) + `data/DATA_VERSION.md`.
- [x] **Fase 4 — Modelado:** [04_FASE4_Modelado.md](./04_FASE4_Modelado.md) + `src/train.py` + comparación de 3 clasificadores y `K-Means`.
- [x] **Fase 5 — Evaluación y Explicabilidad (XAI):** [05_FASE5_Evaluacion_XAI.md](./05_FASE5_Evaluacion_XAI.md) + figuras `04`–`06`.
- [x] **Fase 6 — Despliegue del Sistema y Pruebas:** [06_FASE6_Despliegue_Sistema_y_API.md](./06_FASE6_Despliegue_Sistema_y_API.md) + `app/`, `tests/test_api.py`, `.bat`, `presentation/`.
