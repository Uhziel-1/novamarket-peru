# Fase 4 CRISP-DM — Modelado

> **Script reproducible:** `src/train.py`  
> **Artefactos serializados:** `models/modelo_segmentacion_rfm.joblib`, `models/modelo_recompra_clientes.joblib`, `models/basket_rules.json`

---

## 1. Motor 1 — Recomendador por Reglas de Asociación (Market Basket)

Se indexaron `1,560` reglas verificadas sobre las `18,532` boletas históricas. Ejemplos reales de mayor Lift descubiertos en el conjunto de datos:

| Antecedente (`StockCode`) | Consecuente (`StockCode`) | Co-compras | Confianza | Lift |
| :--- | :--- | :---: | :---: | :---: |
| `Pink Regency Teacup And Saucer` (`22698`) | `Green Regency Teacup And Saucer` (`22697`) | `460` | `82.73 %` | `18.85×` |
| `Green Regency Teacup And Saucer` (`22697`) | `Pink Regency Teacup And Saucer` (`22698`) | `460` | `78.77 %` | `18.85×` |
| `Dolly Girl Lunch Box` (`22629`) | `Spaceboy Lunch Box` (`22630`) | `475` | `66.16 %` | `17.44×` |

Cuando el cliente agrega artículos al carrito en **NovaMarket Perú**, `POST /api/recommend` ordena candidatos no presentes en el carrito por `Lift × Confianza`.

---

## 2. Motor 2A — Segmentación No Supervisada (`K-Means`, `k=4`)

Sobre la matriz `[log1p(recency_days), log1p(frequency), log1p(monetary)]` estandarizada se entrenó `KMeans(n_clusters=4, random_state=42)`, obteniendo los siguientes segmentos comerciales sobre los `3,360` clientes:

| Segmento Comercial | Cantidad de Clientes | Recencia Media | Frecuencia Media | Gasto Medio |
| :--- | :---: | :---: | :---: | :---: |
| **VIP Campeón** | `458` | Baja (compra muy reciente) | Alta | Muy alto |
| **Cliente Leal** | `432` | Moderada-baja | Media-alta | Alto |
| **En Riesgo** | `1,024` | Elevada | Media-baja | Moderado |
| **Dormido / Ocasional** | `1,446` | Muy alta | Baja (`1–2` compras) | Bajo |

---

## 3. Motor 2B — Predicción Supervisada de Recompra (3 Algoritmos)

Sobre los `3,360` clientes (`80 %` entrenamiento con `StratifiedKFold(5)` y `20 %` holdout estratificado) se entrenaron tres pipelines completos (`ColumnTransformer` con `StandardScaler` + `OneHotEncoder`):

1. **Modelo Base (Baseline):** `LogisticRegression` (lineal regularizado).
2. **Modelo de Ensamble Paralelo:** `RandomForestClassifier` ajustado por búsqueda aleatoria (`n_estimators=120`, `max_depth=5`, `min_samples_leaf=5`).
3. **Modelo de Boosting:** `HistGradientBoostingClassifier` (`max_depth=3`, `learning_rate=0.05`).

El criterio de selección automática por validación cruzada (`CV ROC-AUC`) eligió a **`RandomForestClassifier`** (`CV AUC = 0.7426`), serializado en `models/modelo_recompra_clientes.joblib`.
