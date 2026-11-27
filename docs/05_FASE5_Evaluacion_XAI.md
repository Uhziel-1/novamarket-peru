# Fase 5 CRISP-DM — Evaluación y Explicabilidad (XAI)

> **Métricas exactas:** `reports/metrics_summary.json`  
> **Figuras generadas:** `reports/figures/04_reglas_asociacion_lift.png`, `05_roc_y_confusion.png`, `06_shap_clientes.png`

---

## 1. Comparación Cuantitativa en Validación Cruzada y Holdout

| Algoritmo | CV-5 ROC-AUC | Holdout ROC-AUC | Holdout PR-AUC | Holdout F1 | Holdout Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `LogisticRegression (Baseline)` | `0.7394` | `0.7651` | `0.8313` | `0.7358` | `0.7039` |
| **`RandomForestClassifier` (Seleccionado CV)** | **`0.7426`** | **`0.7647`** | **`0.8295`** | **`0.7333`** | **`0.7048`** |
| `HistGradientBoostingClassifier` | `0.7401` | `0.7714` | `0.8337` | `0.7304` | `0.7098` |

---

## 2. Auditoría Honesta Frente al Criterio de Éxito de Fase 1

- En la **Fase 1**, el objetivo técnico inicial planteó alcanzar `ROC-AUC >= 0.78` sin fuga temporal.
- Al evaluar estrictamente la predicción de comportamiento humano a **90 días futuros sin leakage** (`corte 2011-09-09`), los modelos alcanzaron `0.7647` (`RandomForestClassifier`, ganador CV) y `0.7714` (`HistGradientBoostingClassifier`), quedando apenas `0.0086–0.0153` por debajo del umbral ideal de `0.78`, aunque con un **PR-AUC muy sólido (`0.8295–0.8337`)**.
- **Interpretación CRISP-DM:** El modelo ya entrega un ordenamiento comercial altamente accionable para focalizar cupones de retención en clientes *En Riesgo*, y documenta explícitamente que no se introdujeron variables futuras artificiales para inflar el AUC. En una iteración posterior pueden incorporarse variables externas de estacionalidad/feriados del país y categorías favoritas del cliente para cerrar la brecha al `0.78+`.

---

## 3. Explicabilidad Global con SHAP (`06_shap_clientes.png`)

El análisis de valores SHAP (*SHapley Additive exPlanations*) confirma coherencia comercial en las decisiones del modelo ganador:

| Rango | Variable | Importancia Media `|SHAP|` | Lectura de Negocio |
| :---: | :--- | :---: | :--- |
| 1 | `tenure_days` | `0.0609` | Clientes con mayor antigüedad consolidan hábito de recompra. |
| 2 | `monetary` | `0.0468` | Mayor gasto histórico acumulado incrementa la probabilidad de volver. |
| 3 | `recency_days` | `0.0360` | A mayor cantidad de días sin comprar, cae drásticamente la retención. |
| 4 | `frequency` | `0.0329` | Compradores recurrentes mantienen retorno estable. |
| 5 | `total_items` | `0.0250` | Carritos con mayor volumen reflejan fidelización operativa. |
| 6 | `unique_products` | `0.0236` | Explorar varias categorías reduce el riesgo de abandono. |
