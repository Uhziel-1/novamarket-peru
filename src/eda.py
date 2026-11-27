"""
Fase 2 CRISP-DM: Análisis Exploratorio de Datos (EDA) sobre 541,909 transacciones reales.
Minería de Datos - NovaMarket Perú.

Uso:
    python src/eda.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT_DIR / "data" / "raw" / "online_retail.csv"
FIG_DIR = ROOT_DIR / "reports" / "figures"
EDA_JSON = ROOT_DIR / "reports" / "eda_summary.json"


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    df = pd.read_csv(RAW_CSV)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="mixed")

    total_rows = int(len(df))
    null_cust = int(df["CustomerID"].isna().sum())
    null_desc = int(df["Description"].isna().sum())
    cancellations = int(df["InvoiceNo"].astype(str).str.startswith("C").sum())
    bad_qty = int((df["Quantity"] <= 0).sum())
    bad_price = int((df["UnitPrice"] <= 0).sum())

    # Limpieza diagnóstica para analizar ventas válidas
    df_clean = df[
        (~df["InvoiceNo"].astype(str).str.startswith("C"))
        & (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
        & (df["CustomerID"].notna())
        & (df["Description"].notna())
    ].copy()
    df_clean["Description"] = df_clean["Description"].astype(str).str.strip()
    df_clean["TotalAmount"] = df_clean["Quantity"] * df_clean["UnitPrice"]
    df_clean["YearMonth"] = df_clean["InvoiceDate"].dt.to_period("M").astype(str)

    # Figura 1: Auditoría de Calidad de Datos (Antes vs Después de limpieza)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    cats = ["Filas Crudas", "Sin CustomerID", "Cancelaciones ('C')", "Cant./Precio ≤ 0", "Filas Válidas"]
    vals = [total_rows, null_cust, cancellations, int(((df["Quantity"] <= 0) | (df["UnitPrice"] <= 0)).sum()), int(len(df_clean))]
    colors = ["#64748b", "#f59e0b", "#ef4444", "#dc2626", "#16a34a"]
    bars = ax.bar(cats, vals, color=colors)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 8000, f"{v:,}", ha="center", fontweight="bold", fontsize=9.5)
    ax.set_title("Auditoría de Calidad de Datos — Online Retail (541,909 filas crudas)")
    ax.set_ylabel("Cantidad de registros")
    ax.set_ylim(0, total_rows * 1.12)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "01_eda_calidad_datos.png", dpi=150)
    plt.close(fig)

    # Figura 2: Ingresos Mensuales y Boletas Únicas
    monthly = (
        df_clean.groupby("YearMonth", as_index=False)
        .agg(ingresos=("TotalAmount", "sum"), boletas=("InvoiceNo", "nunique"))
        .sort_values("YearMonth")
    )
    fig, ax1 = plt.subplots(figsize=(11, 4.8))
    ax1.bar(monthly["YearMonth"], monthly["ingresos"] / 1000.0, color="#2563eb", alpha=0.82, label="Ingresos (Miles)")
    ax1.set_ylabel("Ingresos (Miles $)", color="#2563eb", fontweight="bold")
    ax1.tick_params(axis="x", rotation=35)
    ax2 = ax1.twinx()
    ax2.plot(monthly["YearMonth"], monthly["boletas"], color="#d97706", marker="o", linewidth=2.4, label="Boletas únicas")
    ax2.set_ylabel("Cantidad de Boletas", color="#d97706", fontweight="bold")
    ax1.set_title("Evolución Mensual de Ventas y Boletas Reales (Dic 2010 – Dic 2011)")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "02_eda_ventas_mensuales.png", dpi=150)
    plt.close(fig)

    # Figura 3: Top 12 Productos por Frecuencia en Boletas
    top_prod = (
        df_clean.groupby("Description", as_index=False)
        .agg(boletas=("InvoiceNo", "nunique"), ingreso=("TotalAmount", "sum"))
        .sort_values("boletas", ascending=False)
        .head(12)
    )
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    sns.barplot(data=top_prod, y="Description", x="boletas", palette="Blues_r", hue="Description", legend=False, ax=ax)
    ax.set_title("Top 12 Productos Más Frecuentes en Boletas Reales")
    ax.set_xlabel("Número de boletas donde aparece")
    ax.set_ylabel("Producto")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "03_eda_top_productos.png", dpi=150)
    plt.close(fig)

    summary = {
        "raw_rows": total_rows,
        "clean_rows": int(len(df_clean)),
        "null_customer_id": null_cust,
        "null_description": null_desc,
        "cancellations": cancellations,
        "invalid_qty_or_price": int(((df["Quantity"] <= 0) | (df["UnitPrice"] <= 0)).sum()),
        "unique_customers": int(df_clean["CustomerID"].nunique()),
        "unique_invoices": int(df_clean["InvoiceNo"].nunique()),
        "unique_products": int(df_clean["StockCode"].nunique()),
        "date_min": str(df_clean["InvoiceDate"].min()),
        "date_max": str(df_clean["InvoiceDate"].max()),
        "total_revenue": round(float(df_clean["TotalAmount"].sum()), 2),
        "monthly_series": [
            {
                "month": str(r.YearMonth),
                "revenue": round(float(r.ingresos), 2),
                "invoices": int(r.boletas),
            }
            for r in monthly.itertuples()
        ],
    }
    with EDA_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("EDA completado:", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
