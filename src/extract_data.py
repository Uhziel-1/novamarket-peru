"""
Extractor reproducible de transacciones reales de e-commerce minorista (Online Retail).
Minería de Datos - NovaMarket Perú (Fase 2 CRISP-DM).

Uso:
    python src/extract_data.py
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd
import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
RAW_CSV = RAW_DIR / "online_retail.csv"
MANIFEST_JSON = RAW_DIR / "extract_manifest.json"

DATASET_URL = (
    "https://raw.githubusercontent.com/databricks/Spark-The-Definitive-Guide/"
    "master/data/retail-data/all/online-retail-dataset.csv"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Descargando dataset real de ventas desde:\n  {DATASET_URL}")

    resp = requests.get(DATASET_URL, timeout=60)
    resp.raise_for_status()
    RAW_CSV.write_bytes(resp.content)

    df = pd.read_csv(RAW_CSV)
    file_hash = sha256_file(RAW_CSV)

    manifest = {
        "schema_version": "1.0",
        "data_version": "1.0.0-raw",
        "extracted_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_url": DATASET_URL,
        "output_file": "data/raw/online_retail.csv",
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "sha256": file_hash,
    }
    with MANIFEST_JSON.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"[OK] Dataset guardado: {RAW_CSV} ({df.shape[0]:,} filas x {df.shape[1]} columnas)")
    print(f"     SHA-256: {file_hash}")
    print(df.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
