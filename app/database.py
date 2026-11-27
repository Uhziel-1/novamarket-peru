"""
Persistencia SQLite para boletas y ventas de NovaMarket Perú.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT_DIR / "data" / "novamarket.db"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS boletas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                segmento TEXT NOT NULL,
                items_json TEXT NOT NULL,
                items_count INTEGER NOT NULL,
                total_usd REAL NOT NULL,
                total_pen REAL NOT NULL,
                exchange_rate REAL NOT NULL,
                used_recommendation INTEGER NOT NULL DEFAULT 0,
                creado_en TEXT NOT NULL
            )
            """
        )
        conn.commit()


def insert_boleta(
    customer_id: int,
    segmento: str,
    items: List[Dict],
    total_usd: float,
    total_pen: float,
    exchange_rate: float,
    used_recommendation: bool = False,
    db_path: Path = DEFAULT_DB_PATH,
) -> Dict:
    creado_en = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    items_count = sum(int(it.get("quantity", 1)) for it in items)
    with get_connection(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO boletas
            (customer_id, segmento, items_json, items_count, total_usd, total_pen, exchange_rate, used_recommendation, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(customer_id),
                segmento,
                json.dumps(items, ensure_ascii=False),
                items_count,
                round(float(total_usd), 2),
                round(float(total_pen), 2),
                round(float(exchange_rate), 4),
                1 if used_recommendation else 0,
                creado_en,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM boletas WHERE id = ?", (cur.lastrowid,)).fetchone()
    d = dict(row)
    d["items"] = json.loads(d.pop("items_json"))
    d["used_recommendation"] = bool(d["used_recommendation"])
    return d


def list_boletas(limit: int = 30, db_path: Path = DEFAULT_DB_PATH) -> List[Dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM boletas ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["items"] = json.loads(d.pop("items_json"))
        d["used_recommendation"] = bool(d["used_recommendation"])
        out.append(d)
    return out
