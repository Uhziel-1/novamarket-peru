# Fase 2 CRISP-DM — Comprensión de los Datos (EDA)

> **Script reproducible:** `src/eda.py`  
> **Salida cuantitativa:** `reports/eda_summary.json`  
> **Figuras generadas:** `reports/figures/01_eda_calidad_datos.png`, `02_eda_ventas_mensuales.png`, `03_eda_top_productos.png`

---

## 1. Recolección y Linaje Inicial

- **Archivo origen:** `data/raw/online_retail.csv` (extraído por `src/extract_data.py`).
- **Volumen bruto:** `541,909` líneas de boleta y `8` columnas (`InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country`).
- **Ventana temporal:** `2010-12-01 08:26:00` hasta `2011-12-09 12:50:00`.
- **Integridad SHA-256:** `a2f79bbdd4463df6db8a3f5a50b9c980ae8f645a370bf5e2c0d6097f9e817b05`.

---

## 2. Auditoría de Calidad de Datos

La inspección sistemática detectó cuatro anomalías operativas que invalidan cualquier entrenamiento directo sobre la tabla cruda:

| Anomalía Detectada | Conteo de Filas | Impacto en Minería de Datos |
| :--- | :---: | :--- |
| **`CustomerID` nulo** | `135,080` (`24.9 %`) | Imposible construir trayectoria RFM o recompra sin identificar al cliente. |
| **Cantidades o precios `<= 0`** | `11,805` | Ajustes contables y precios cero distorsionan el gasto monetario (*Monetary*). |
| **Notas de crédito / Cancelaciones (`InvoiceNo` con prefijo `C`)** | `9,288` | Devoluciones; mezclarlas con ventas reales inflaría co-ocurrencias del recomendador. |
| **`Description` nulo** | `1,454` | Ítems sin nombre utilizable en el buscador ni catálogo. |

Tras depurar registros válidos con cliente e importe positivo, el EDA reporta `397,884` líneas limpias (`4,338` clientes únicos, `18,532` boletas únicas, `3,665` productos distintos y un ingreso bruto auditado de `$8,911,407.90`).

---

## 3. Hallazgos Exploratorios Clave

1. **Estacionalidad fuerte (`02_eda_ventas_mensuales.png`):** La facturación escala en el último trimestre (septiembre–noviembre 2011), lo que exige particionar entrenamiento y evaluación por fecha real y no aleatoriamente.
2. **Concentración de catálogo (`03_eda_top_productos.png`):** Un núcleo de productos de alta rotación domina la frecuencia en boletas, ideal para extraer reglas de asociación de alto soporte y servir como catálogo principal del POS (`150` SKUs).
