# agent/tools/finance_utils.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from dateutil import parser as dateparser
import pandas as pd

# --- Month handling ---------------------------------------------------------

def parse_month_to_period(value: str | int | datetime) -> pd.Period:
    """
    Parse strings like '2025-06', 'June 2025', '2025/06' -> pandas.Period('M').
    """
    if isinstance(value, pd.Period):
        return value.asfreq("M")
    if isinstance(value, (datetime, pd.Timestamp)):
        return pd.Period(value, freq="M")
    s = str(value).strip()
    # fast path for YYYY-MM
    try:
        return pd.Period(s, freq="M")
    except Exception:
        dt = dateparser.parse(s, dayfirst=False, yearfirst=False, default=datetime(2000, 1, 1))
        return pd.Period(pd.Timestamp(dt), freq="M")

def normalize_month_column(df: pd.DataFrame, col: str = "month") -> pd.DataFrame:
    df = df.copy()
    df[col] = df[col].map(parse_month_to_period)
    return df

# --- Safe math / formatting -------------------------------------------------

def safe_pct(numer: float, denom: float) -> float | None:
    """Return numer/denom as float; None if denom==0."""
    return None if denom == 0 else float(numer) / float(denom)

def fmt_money(v: float) -> str:
    """Compact money format in USD."""
    neg = v < 0
    x = abs(float(v))
    if x >= 1_000_000_000:
        s = f"${x/1_000_000_000:.2f}B"
    elif x >= 1_000_000:
        s = f"${x/1_000_000:.2f}M"
    elif x >= 1_000:
        s = f"${x/1_000:.2f}k"
    else:
        s = f"${x:,.0f}"
    return f"-{s}" if neg else s

def fmt_pct(p: float | None) -> str:
    if p is None:
        return "N/A"
    return f"{p*100:.1f}%"
