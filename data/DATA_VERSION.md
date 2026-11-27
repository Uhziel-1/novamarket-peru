# Versionado y Linaje de Datos (`NovaMarket Perú`)

| Versión | Archivo | Descripción | Filas | SHA-256 |
| :--- | :--- | :--- | :---: | :--- |
| `v1.0.0-raw` | `data/raw/online_retail.csv` | Boletas reales Online Retail descargadas por `src/extract_data.py`. | 541,909 | `a2f79bbdd4463df6db8a3f5a50b9c980ae8f645a370bf5e2c0d6097f9e817b05` |
| `v2.0.0-clean` | `data/processed/retail_clean_transactions.csv` | Sin cancelaciones (`C`), sin cantidades/precios ≤ 0 ni `CustomerID` nulo. | 396,337 | `59415669e3f795060865281f61ba42e3fb01f4eee6373b16944dd5fa0df1bc09` |
| `v2.0.0-rfm` | `data/processed/rfm_customers_dataset.csv` | Características RFM causales (`< 2011-09-09`) + target recompra futura (`≥ 2011-09-09`). | 3,360 | `11f6fefbc5b6310b9377d69c59363e1aa40e98e25549aaa8c79e8c4b51486a90` |

* **Modelo ganador:** `RandomForestClassifier` (`SHA-256: 2f0f818a1533a881c07ae167fd8b72a5ac836fea9fe14ebb680ad9908a9eeb90`)
