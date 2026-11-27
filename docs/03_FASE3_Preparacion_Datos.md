# Fase 3 CRISP-DM — Preparación de Datos e Ingeniería de Características

> **Script reproducible:** `src/train.py`  
> **Artefactos generados:** `data/processed/retail_clean_transactions.csv`, `data/processed/rfm_customers_dataset.csv`, `data/DATA_VERSION.md`

---

## 1. Limpieza Transaccional (`v2.0.0-clean`)

Sobre las `541,909` filas originales, se aplicó un filtro estricto para obtener `396,337` registros limpios (`SHA-256: 59415669e3f795060865281f61ba42e3fb01f4eee6373b16944dd5fa0df1bc09`):
1. Exclusión de cancelaciones (`~InvoiceNo.str.startswith("C")`), guardando el conteo de cancelaciones por cliente como señal de riesgo antes de retirarlas.
2. Eliminación de `CustomerID` nulos, descripciones nulas y registros con `Quantity <= 0` o `UnitPrice <= 0`.
3. Exclusión de códigos administrativos no comerciales (`POST`, `DOT`, `M`, `BANK CHARGES`, `D`, `CRUK`, etc.).
4. Normalización de descripciones y categorización comercial multirubro en español para la tienda web (`150` SKUs activos).

---

## 2. Rama A — Matriz de Co-Ocurrencias para Reglas de Asociación

- Cada `InvoiceNo` se trata como una **canasta de compra** sobre los `150` productos del catálogo (`models/catalog_products.json`).
- Para cada par `(Antecedente A -> Consecuente B)` se computa:
  - **Soporte:** proporción de boletas que contienen `A` y `B`.
  - **Confianza:** $P(B \mid A) = \frac{\text{boletas}(A \cap B)}{\text{boletas}(A)}$.
  - **Lift:** $\frac{P(B \mid A)}{P(B)}$ (fuerza real de asociación por encima del azar).
- Se retuvieron **`1,560` reglas robustas** con `Confianza >= 15 %` y `Lift >= 1.5`, almacenadas en `models/basket_rules.json` y `reports/top_association_rules.csv`.

---

## 3. Rama B — Ingeniería RFM Sin Fuga Temporal (`v2.0.0-rfm`)

Para predecir **si un cliente volverá a comprar en los próximos 90 días**, se fijó una **fecha de corte estricta: `2011-09-09`**:

- **Ventana de observación (`< 2011-09-09`, `3,360` clientes):**
  - `recency_days`: días desde la última boleta del cliente hasta el `2011-09-09`.
  - `frequency`: total de boletas únicas acumuladas antes del corte.
  - `monetary`: gasto total acumulado en USD antes del corte.
  - `avg_basket_value`: gasto promedio por boleta.
  - `total_items` y `unique_products`: volumen y amplitud de categorías adquiridas.
  - `tenure_days` y `purchase_velocity`: antigüedad del cliente y ritmo mensual de compra.
  - `cancellation_count`: cancelaciones históricas registradas antes del corte.
  - `is_uk`: origen geográfico (`UK` vs `Internacional`).
- **Variable objetivo (`>= 2011-09-09`):** `recompra_90d = 1` si el cliente generó al menos una boleta válida en los últimos 3 meses (`57.11 %` positivos), `0` en caso contrario.

> **Garantía anti-leakage:** Ningún dato posterior al `2011-09-09` interviene en las variables `X` ni en el ajuste de los transformadores `StandardScaler` o `OneHotEncoder`.
