"""
Cliente de APIs externas en vivo para NovaMarket Perú:
    1. Tipo de cambio USD -> PEN (open.er-api.com)
    2. Feriados nacionales en Perú (date.nager.at)
Incluye caché en memoria y respaldo seguro si no hay conexión.
"""

from datetime import datetime
import time
from typing import Any, Dict
from zoneinfo import ZoneInfo

import requests

FX_URL = "https://open.er-api.com/v6/latest/USD"
HOLIDAYS_URL = "https://date.nager.at/api/v3/PublicHolidays/2026/PE"

_CACHE: Dict[str, Any] = {"ts": 0.0, "data": None}


def get_external_context() -> Dict[str, Any]:
    now_ts = time.time()
    if _CACHE["data"] is not None and (now_ts - _CACHE["ts"]) < 900:
        return _CACHE["data"]

    rate_pen = 3.75
    fx_source = "Respaldo Local"
    fx_updated = "N/A"

    try:
        r = requests.get(FX_URL, timeout=6)
        r.raise_for_status()
        j = r.json()
        pen = j.get("rates", {}).get("PEN")
        if pen:
            rate_pen = round(float(pen), 4)
            fx_source = "open.er-api.com (En Vivo)"
            fx_updated = str(j.get("time_last_update_utc", ""))[:16]
    except Exception:
        pass

    today_lima = datetime.now(ZoneInfo("America/Lima")).strftime("%Y-%m-%d")
    is_holiday = False
    holiday_name = None
    next_holiday = None
    hol_source = "Respaldo Local"

    try:
        rh = requests.get(HOLIDAYS_URL, timeout=6)
        rh.raise_for_status()
        holidays = rh.json()
        hol_source = "date.nager.at (En Vivo)"
        for h in holidays:
            if h.get("date") == today_lima:
                is_holiday = True
                holiday_name = h.get("localName") or h.get("name")
            if h.get("date", "") >= today_lima and next_holiday is None:
                next_holiday = f"{h.get('date')} ({h.get('localName') or h.get('name')})"
    except Exception:
        pass

    ctx = {
        "usd_to_pen": rate_pen,
        "fx_source": fx_source,
        "fx_updated": fx_updated,
        "today_lima": today_lima,
        "is_holiday": is_holiday,
        "holiday_name": holiday_name,
        "next_holiday": next_holiday or "Campaña Navideña",
        "holidays_source": hol_source,
    }
    _CACHE["ts"] = now_ts
    _CACHE["data"] = ctx
    return ctx
