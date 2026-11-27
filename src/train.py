"""
Fases 3, 4 y 5 CRISP-DM: Limpieza, Reglas de Asociación, Clustering RFM,
Modelado Supervisado (Recompra/Fuga), Evaluación y XAI (SHAP).
Minería de Datos - NovaMarket Perú.

Uso:
    python src/train.py
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Tuple

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import sklearn
from sklearn.base import clone
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
CUTOFF_DATE = "2011-09-09"
ROOT_DIR = Path(__file__).resolve().parent.parent

RAW_CSV = ROOT_DIR / "data" / "raw" / "online_retail.csv"
PROC_CLEAN_CSV = ROOT_DIR / "data" / "processed" / "retail_clean_transactions.csv"
PROC_RFM_CSV = ROOT_DIR / "data" / "processed" / "rfm_customers_dataset.csv"
DATA_VERSION_MD = ROOT_DIR / "data" / "DATA_VERSION.md"
MANIFEST_JSON = ROOT_DIR / "data" / "dataset_manifest.json"

MODELS_DIR = ROOT_DIR / "models"
CATALOG_JSON = MODELS_DIR / "catalog_products.json"
RULES_JSON = MODELS_DIR / "basket_rules.json"
CUSTOMERS_JSON = MODELS_DIR / "sample_customers.json"
RFM_MODEL_PATH = MODELS_DIR / "modelo_segmentacion_rfm.joblib"
CHURN_MODEL_PATH = MODELS_DIR / "modelo_recompra_clientes.joblib"

FIG_DIR = ROOT_DIR / "reports" / "figures"
METRICS_JSON = ROOT_DIR / "reports" / "metrics_summary.json"
RULES_CSV = ROOT_DIR / "reports" / "top_association_rules.csv"

ADMIN_CODES = {"POST", "DOT", "M", "BANK CHARGES", "PADS", "C2", "CRUK", "D"}

RFM_NUM_FEATURES = [
    "recency_days",
    "frequency",
    "monetary",
    "avg_basket_value",
    "total_items",
    "unique_products",
    "tenure_days",
    "purchase_velocity",
    "cancellation_count",
]
RFM_CAT_FEATURES = ["is_uk"]
RFM_ALL_FEATURES = RFM_NUM_FEATURES + RFM_CAT_FEATURES


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def infer_category(desc: str) -> str:
    d = desc.upper()
    if any(k in d for k in ["BAG", "LUNCH", "POUCH", "TOTE", "SHOPPER"]):
        return "Bolsos y Viaje"
    if any(k in d for k in ["MUG", "CUP", "TEA", "PLATE", "BOWL", "CAKE", "JAR", "TIN", "KITCHEN"]):
        return "Cocina y Mesa"
    if any(k in d for k in ["LIGHT", "LANTERN", "CANDLE", "HOLDER", "CLOCK", "FRAME", "HEART"]):
        return "Hogar y Decoración"
    if any(k in d for k in ["CARD", "NOTEBOOK", "PEN", "PAPER", "WRAP", "TAPE", "BOOK", "CALENDAR"]):
        return "Oficina y Papelería"
    if any(k in d for k in ["CHRISTMAS", "BUNTING", "PARTY", "RIBBON", "GIFT", "TOY"]):
        return "Regalos y Eventos"
    return "Accesorios y Varios"


def build_market_basket(df_clean: pd.DataFrame) -> Tuple[List[Dict], Dict[str, List[Dict]], pd.DataFrame]:
    """Construye el catálogo top 150 y reglas de asociación reales (Soporte, Confianza, Lift)."""
    prod_stats = (
        df_clean.groupby(["StockCode", "Description"], as_index=False)
        .agg(
            invoice_count=("InvoiceNo", "nunique"),
            units_sold=("Quantity", "sum"),
            price_usd=("UnitPrice", "median"),
            revenue_usd=("TotalAmount", "sum"),
        )
        .sort_values("invoice_count", ascending=False)
    )
    # Quedarse con 1 descripción canónica por StockCode y top 150 productos activos
    prod_stats = prod_stats.drop_duplicates(subset=["StockCode"]).head(150).reset_index(drop=True)
    top_codes = set(prod_stats["StockCode"])

    catalog: List[Dict] = []
    code_to_meta: Dict[str, Dict] = {}
    for row in prod_stats.itertuples():
        item = {
            "stock_code": str(row.StockCode),
            "description": str(row.Description).title(),
            "category": infer_category(str(row.Description)),
            "price_usd": round(max(0.5, float(row.price_usd)), 2),
            "invoice_count": int(row.invoice_count),
            "units_sold": int(row.units_sold),
        }
        catalog.append(item)
        code_to_meta[item["stock_code"]] = item

    # Matriz binaria Boleta x Producto sobre todas las boletas que contengan al menos 1 de los top 150
    df_top = df_clean[df_clean["StockCode"].isin(top_codes)][["InvoiceNo", "StockCode"]].drop_duplicates()
    basket = pd.crosstab(df_top["InvoiceNo"], df_top["StockCode"]).astype(np.int32)
    n_invoices = len(basket)
    mat = basket.values
    co_occ = mat.T @ mat
    item_counts = np.diag(co_occ)
    codes = basket.columns.tolist()

    rules_rows: List[Dict] = []
    rules_by_product: Dict[str, List[Dict]] = {c: [] for c in codes}

    for i, code_a in enumerate(codes):
        cnt_a = int(item_counts[i])
        if cnt_a < 25:
            continue
        candidates_for_a: List[Dict] = []
        for j, code_b in enumerate(codes):
            if i == j:
                continue
            cnt_ab = int(co_occ[i, j])
            if cnt_ab < 20:
                continue
            cnt_b = int(item_counts[j])
            sup_ab = cnt_ab / n_invoices
            conf = cnt_ab / cnt_a
            sup_b = cnt_b / n_invoices
            lift = conf / sup_b
            if conf >= 0.15 and lift >= 1.5:
                meta_b = code_to_meta[code_b]
                rule = {
                    "antecedent": code_a,
                    "antecedent_name": code_to_meta[code_a]["description"],
                    "consequent": code_b,
                    "consequent_name": meta_b["description"],
                    "consequent_category": meta_b["category"],
                    "consequent_price_usd": meta_b["price_usd"],
                    "co_purchases": cnt_ab,
                    "support": round(sup_ab, 4),
                    "confidence": round(conf, 4),
                    "lift": round(lift, 2),
                }
                rules_rows.append(rule)
                candidates_for_a.append(rule)

        candidates_for_a.sort(key=lambda r: (r["lift"] * r["confidence"]), reverse=True)
        rules_by_product[code_a] = candidates_for_a[:5]

    rules_df = pd.DataFrame(rules_rows).sort_values(["lift", "confidence"], ascending=False)
    return catalog, rules_by_product, rules_df


def build_rfm_dataset(df_all: pd.DataFrame, df_clean: pd.DataFrame) -> pd.DataFrame:
    """Construye dataset causal de clientes (< CUTOFF_DATE) con target de recompra (>= CUTOFF_DATE)."""
    cutoff = pd.Timestamp(CUTOFF_DATE)

    past_clean = df_clean[df_clean["InvoiceDate"] < cutoff]
    future_clean = df_clean[df_clean["InvoiceDate"] >= cutoff]
    past_cancels = df_all[
        (df_all["InvoiceDate"] < cutoff)
        & (df_all["InvoiceNo"].astype(str).str.startswith("C"))
        & (df_all["CustomerID"].notna())
    ]

    cancel_counts = past_cancels.groupby("CustomerID")["InvoiceNo"].nunique().to_dict()
    future_buyers = set(future_clean["CustomerID"].unique())

    cust = past_clean.groupby("CustomerID", as_index=False).agg(
        last_purchase=("InvoiceDate", "max"),
        first_purchase=("InvoiceDate", "min"),
        frequency=("InvoiceNo", "nunique"),
        monetary=("TotalAmount", "sum"),
        total_items=("Quantity", "sum"),
        unique_products=("StockCode", "nunique"),
        country=("Country", "first"),
    )

    cust["recency_days"] = (cutoff - cust["last_purchase"]).dt.days.astype(int)
    cust["tenure_days"] = (cust["last_purchase"] - cust["first_purchase"]).dt.days.astype(int)
    cust["avg_basket_value"] = (cust["monetary"] / cust["frequency"]).round(2)
    cust["purchase_velocity"] = (cust["frequency"] / ((cust["tenure_days"] / 30.0) + 1.0)).round(3)
    cust["cancellation_count"] = cust["CustomerID"].map(lambda cid: int(cancel_counts.get(cid, 0)))
    cust["is_uk"] = np.where(cust["country"] == "United Kingdom", "UK", "Internacional")
    cust["will_repurchase"] = cust["CustomerID"].isin(future_buyers).astype(int)
    cust["CustomerID"] = cust["CustomerID"].astype(int)
    cust["monetary"] = cust["monetary"].round(2)

    cols = ["CustomerID", "country"] + RFM_ALL_FEATURES + ["will_repurchase"]
    return cust[cols].reset_index(drop=True)


def build_preprocessor(scale_num: bool) -> ColumnTransformer:
    num_steps = [("imputer", SimpleImputer(strategy="median"))]
    if scale_num:
        num_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer(
        transformers=[
            ("num", Pipeline(num_steps), RFM_NUM_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), RFM_CAT_FEATURES),
        ],
        verbose_feature_names_out=False,
    )


def evaluate_binary(y_true: np.ndarray, probs: np.ndarray) -> Dict[str, float]:
    preds = (probs >= 0.5).astype(int)
    return {
        "roc_auc": round(float(roc_auc_score(y_true, probs)), 4),
        "pr_auc": round(float(average_precision_score(y_true, probs)), 4),
        "f1": round(float(f1_score(y_true, preds)), 4),
        "precision": round(float(precision_score(y_true, preds)), 4),
        "recall": round(float(recall_score(y_true, preds)), 4),
        "accuracy": round(float(accuracy_score(y_true, preds)), 4),
    }


def main() -> None:
    np.random.seed(SEED)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    PROC_CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("CRISP-DM FASES 3-5: NOVAMARKET PERÚ (REGLAS + RFM + RECOMPRA + SHAP)")
    print("=" * 72)

    df_all = pd.read_csv(RAW_CSV)
    df_all["InvoiceDate"] = pd.to_datetime(df_all["InvoiceDate"], format="mixed")
    raw_hash = sha256_file(RAW_CSV)

    # Limpieza estricta de transacciones válidas
    df_clean = df_all[
        (~df_all["InvoiceNo"].astype(str).str.startswith("C"))
        & (df_all["Quantity"] > 0)
        & (df_all["UnitPrice"] > 0)
        & (df_all["CustomerID"].notna())
        & (df_all["Description"].notna())
        & (~df_all["StockCode"].astype(str).isin(ADMIN_CODES))
    ].copy()
    df_clean["StockCode"] = df_clean["StockCode"].astype(str).str.strip()
    df_clean["Description"] = df_clean["Description"].astype(str).str.strip()
    df_clean["TotalAmount"] = (df_clean["Quantity"] * df_clean["UnitPrice"]).round(2)
    df_clean.to_csv(PROC_CLEAN_CSV, index=False)
    clean_hash = sha256_file(PROC_CLEAN_CSV)

    # 1. Motor A: Reglas de Asociación (Recomendador de Carrito)
    catalog, rules_by_product, rules_df = build_market_basket(df_clean)
    CATALOG_JSON.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    RULES_JSON.write_text(json.dumps(rules_by_product, indent=2, ensure_ascii=False), encoding="utf-8")
    rules_df.head(50).to_csv(RULES_CSV, index=False)
    print(f"[Motor 1] Catálogo: {len(catalog)} productos | Reglas válidas (Conf≥15%, Lift≥1.5): {len(rules_df):,}")

    # Figura 4: Top 10 Reglas de Asociación por Lift
    top_r = rules_df.head(10).copy()
    top_r["pair"] = top_r["antecedent_name"].str[:18] + " → " + top_r["consequent_name"].str[:18]
    fig, ax = plt.subplots(figsize=(10.5, 5))
    bars = ax.barh(top_r["pair"][::-1], top_r["lift"][::-1], color="#2563eb")
    for b, conf in zip(bars, top_r["confidence"][::-1]):
        ax.text(b.get_width() + 0.15, b.get_y() + b.get_height() / 2, f"Conf: {conf*100:.0f}%", va="center", fontsize=9)
    ax.set_title("Top 10 Reglas de Asociación en Boletas Reales (ordenadas por Lift)")
    ax.set_xlabel("Lift (veces más probable que al azar)")
    ax.set_xlim(0, float(top_r["lift"].max()) * 1.2)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "04_reglas_asociacion_lift.png", dpi=150)
    plt.close(fig)

    # 2. Motor B: Dataset RFM causal + Clustering K-Means + Predicción Recompra
    df_rfm = build_rfm_dataset(df_all, df_clean)
    df_rfm.to_csv(PROC_RFM_CSV, index=False)
    rfm_hash = sha256_file(PROC_RFM_CSV)

    X = df_rfm[RFM_ALL_FEATURES]
    y = df_rfm["will_repurchase"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=SEED
    )
    print(f"[Motor 2] Clientes RFM (< {CUTOFF_DATE}): {len(df_rfm):,} | Tasa recompra futura: {y.mean():.4f}")

    # Segmentación K-Means (4 segmentos sobre log1p(Recency, Frequency, Monetary))
    rfm_log = np.log1p(df_rfm[["recency_days", "frequency", "monetary"]].clip(lower=0))
    kmeans_pipe = Pipeline([("scaler", StandardScaler()), ("kmeans", KMeans(n_clusters=4, random_state=SEED, n_init=10))])
    clusters = kmeans_pipe.fit_predict(rfm_log)
    df_rfm["cluster_id"] = clusters

    # Etiquetar clusters objetivamente según puntuación RFM (menor recency, mayor frequency y monetary)
    cent = df_rfm.groupby("cluster_id")[["recency_days", "frequency", "monetary"]].mean()
    cent["score"] = (
        cent["frequency"].rank(pct=True)
        + cent["monetary"].rank(pct=True)
        + (1.0 - cent["recency_days"].rank(pct=True))
    )
    ordered_ids = cent.sort_values("score", ascending=False).index.tolist()
    labels_ordered = ["VIP Campeón", "Cliente Leal", "En Riesgo", "Dormido / Ocasional"]
    cluster_map = {int(cid): lbl for cid, lbl in zip(ordered_ids, labels_ordered)}
    df_rfm["segmento"] = df_rfm["cluster_id"].map(cluster_map)
    joblib.dump({"pipeline": kmeans_pipe, "cluster_map": cluster_map}, RFM_MODEL_PATH)

    # Comparativa de 3 modelos con StratifiedKFold(5)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    lr_search = RandomizedSearchCV(
        Pipeline([("pre", build_preprocessor(True)), ("model", LogisticRegression(max_iter=1000, random_state=SEED))]),
        {"model__C": [0.05, 0.1, 1.0, 5.0]},
        n_iter=4, cv=cv, scoring="roc_auc", refit=True, random_state=SEED, n_jobs=-1,
    )
    rf_search = RandomizedSearchCV(
        Pipeline([("pre", build_preprocessor(False)), ("model", RandomForestClassifier(random_state=SEED, n_jobs=-1))]),
        {"model__n_estimators": [120, 200], "model__max_depth": [5, 8, 12], "model__min_samples_leaf": [5, 15, 30]},
        n_iter=8, cv=cv, scoring="roc_auc", refit=True, random_state=SEED, n_jobs=-1,
    )
    hgb_search = RandomizedSearchCV(
        Pipeline([("pre", build_preprocessor(False)), ("model", HistGradientBoostingClassifier(random_state=SEED))]),
        {"model__learning_rate": [0.03, 0.05, 0.1], "model__max_iter": [120, 200], "model__max_depth": [3, 5, 7], "model__min_samples_leaf": [20, 40, 80]},
        n_iter=10, cv=cv, scoring="roc_auc", refit=True, random_state=SEED, n_jobs=-1,
    )

    candidates: Dict[str, Any] = {
        "LogisticRegression (Baseline)": lr_search,
        "RandomForestClassifier": rf_search,
        "HistGradientBoostingClassifier": hgb_search,
    }

    comparison = []
    roc_data = {}
    best_name, best_cv, best_search = None, -1.0, None

    for name, search in candidates.items():
        t0 = time.time()
        search.fit(X_train, y_train)
        elapsed = time.time() - t0
        probs = search.best_estimator_.predict_proba(X_test)[:, 1]
        metrics = evaluate_binary(y_test, probs)
        fpr, tpr, _ = roc_curve(y_test, probs)
        roc_data[name] = (fpr, tpr, metrics["roc_auc"])
        row = {"model": name, "cv_roc_auc": round(float(search.best_score_), 4), "fit_seconds": round(elapsed, 2), "best_params": search.best_params_, **metrics}
        comparison.append(row)
        print(f"  {name:32s} | CV AUC={row['cv_roc_auc']:.4f} | Holdout AUC={row['roc_auc']:.4f} | F1={row['f1']:.4f}")
        if search.best_score_ > best_cv:
            best_cv, best_name, best_search = search.best_score_, name, search

    best_est = best_search.best_estimator_
    best_probs = best_est.predict_proba(X_test)[:, 1]
    best_preds = (best_probs >= 0.5).astype(int)

    # Figura 5: ROC + Matriz de Confusión combinadas en una figura nítida
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for name, (fpr, tpr, auc_v) in roc_data.items():
        axes[0].plot(fpr, tpr, linewidth=2.2, label=f"{name} (AUC={auc_v:.4f})")
    axes[0].plot([0, 1], [0, 1], "k--", alpha=0.5)
    axes[0].set_title("Curvas ROC en Holdout de Clientes (25 %)")
    axes[0].set_xlabel("FPR")
    axes[0].set_ylabel("TPR")
    axes[0].legend(loc="lower right", fontsize=8.5)
    axes[0].grid(alpha=0.3)

    cm = confusion_matrix(y_test, best_preds)
    ConfusionMatrixDisplay(cm, display_labels=["No Recompra", "Recompra"]).plot(cmap="Blues", ax=axes[1], values_format="d")
    axes[1].set_title(f"Matriz de Confusión — {best_name}")
    plt.tight_layout()
    fig.savefig(FIG_DIR / "05_roc_y_confusion.png", dpi=150)
    plt.close(fig)

    # Figura 6: SHAP Explicabilidad del Predictor de Recompra
    pre_f = best_est.named_steps["pre"]
    mod_f = best_est.named_steps["model"]
    X_test_t = pre_f.transform(X_test)
    feat_names = pre_f.get_feature_names_out()
    if isinstance(mod_f, LogisticRegression):
        explainer = shap.LinearExplainer(mod_f, pre_f.transform(X_train))
        sv = explainer(X_test_t)
        vals = sv.values
    else:
        explainer = shap.TreeExplainer(mod_f)
        sv = explainer(X_test_t)
        vals = sv.values[:, :, 1] if sv.values.ndim == 3 else sv.values

    shap_df = pd.DataFrame({"feature": feat_names, "mean_abs_shap": np.abs(vals).mean(axis=0)}).sort_values("mean_abs_shap", ascending=False).round(4)
    plt.figure(figsize=(9.5, 5.2))
    shap.summary_plot(vals, X_test_t, feature_names=feat_names, max_display=10, show=False)
    plt.title(f"SHAP Summary (Top 10 Drivers de Recompra) — {best_name}")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "06_shap_clientes.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Refit final sobre todos los clientes RFM y guardar clientes reales de muestra para la UI
    final_model = clone(best_est)
    final_model.fit(X, y)
    joblib.dump(final_model, CHURN_MODEL_PATH)
    model_hash = sha256_file(CHURN_MODEL_PATH)

    # Seleccionar 24 clientes reales representativos (6 por cada segmento)
    sample_custs = []
    for seg in labels_ordered:
        sub = df_rfm[df_rfm["segmento"] == seg].sort_values("monetary", ascending=False).head(6)
        for r in sub.to_dict(orient="records"):
            sample_custs.append(r)
    CUSTOMERS_JSON.write_text(json.dumps(sample_custs, indent=2, ensure_ascii=False), encoding="utf-8")

    metrics_payload = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": SEED,
        "cutoff_date": CUTOFF_DATE,
        "total_customers_rfm": int(len(df_rfm)),
        "repurchase_rate": round(float(y.mean()), 4),
        "catalog_products": int(len(catalog)),
        "association_rules_count": int(len(rules_df)),
        "segment_counts": df_rfm["segmento"].value_counts().to_dict(),
        "winner_model": best_name,
        "winner_params": best_search.best_params_,
        "model_comparison": comparison,
        "top_shap_importance": shap_df.head(8).to_dict(orient="records"),
    }
    METRICS_JSON.write_text(json.dumps(metrics_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "data_version": "2.0.0-retail-rfm",
        "generated_at_utc": metrics_payload["generated_at_utc"],
        "raw_dataset": {"path": "data/raw/online_retail.csv", "sha256": raw_hash},
        "clean_transactions": {"path": "data/processed/retail_clean_transactions.csv", "rows": int(len(df_clean)), "sha256": clean_hash},
        "rfm_dataset": {"path": "data/processed/rfm_customers_dataset.csv", "rows": int(len(df_rfm)), "sha256": rfm_hash},
        "model_artifact": {"path": "models/modelo_recompra_clientes.joblib", "algorithm": best_name, "sha256": model_hash},
    }
    MANIFEST_JSON.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    DATA_VERSION_MD.write_text(
        f"""# Versionado y Linaje de Datos (`NovaMarket Perú`)

| Versión | Archivo | Descripción | Filas | SHA-256 |
| :--- | :--- | :--- | :---: | :--- |
| `v1.0.0-raw` | `data/raw/online_retail.csv` | Boletas reales Online Retail descargadas por `src/extract_data.py`. | {len(df_all):,} | `{raw_hash}` |
| `v2.0.0-clean` | `data/processed/retail_clean_transactions.csv` | Sin cancelaciones (`C`), sin cantidades/precios ≤ 0 ni `CustomerID` nulo. | {len(df_clean):,} | `{clean_hash}` |
| `v2.0.0-rfm` | `data/processed/rfm_customers_dataset.csv` | Características RFM causales (`< {CUTOFF_DATE}`) + target recompra futura (`≥ {CUTOFF_DATE}`). | {len(df_rfm):,} | `{rfm_hash}` |

* **Modelo ganador:** `{best_name}` (`SHA-256: {model_hash}`)
""",
        encoding="utf-8",
    )

    print(f"\n[OK] Ganador: {best_name} | Top SHAP:\n{shap_df.head(5).to_string(index=False)}")
    print("=" * 72)


if __name__ == "__main__":
    main()
