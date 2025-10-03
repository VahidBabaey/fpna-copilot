# agent/intent_router.py
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any, List
import pandas as pd
from agent.tools.finance_utils import parse_month_to_period

Intent = Literal["revenue_vs_budget", "gross_margin_trend", "opex_breakdown", "cash_runway"]

MONTH_RX = re.compile(r"\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
                      r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|"
                      r"dec(?:ember)?)\s+\d{4}\b", re.I)
YM_RX = re.compile(r"\b(20\d{2})[-/ ](0?[1-9]|1[0-2])\b")

def _find_single_month(text: str) -> Optional[pd.Period]:
    s = text.strip()
    m1 = MONTH_RX.search(s)
    if m1:
        return parse_month_to_period(m1.group(0))
    m2 = YM_RX.search(s)
    if m2:
        y, mm = int(m2.group(1)), int(m2.group(2))
        return pd.Period(f"{y:04d}-{mm:02d}", freq="M")
    return None

def _find_last_n_months(text: str) -> Optional[int]:
    m = re.search(r"last\s+(\d+)\s+months?", text, re.I)
    if m:
        return int(m.group(1))
    # default for “trend” without number → 3 months
    if re.search(r"\btrend\b", text, re.I):
        return 3
    return None

def route_intent(text: str) -> Dict[str, Any]:
    """Return {'intent': ..., 'month': Period|None, 'last_n': int|None}"""
    t = text.strip().lower()

    if "cash" in t and "runway" in t:
        return {"intent": "cash_runway", "month": None, "last_n": None}

    if "revenue" in t and ("budget" in t or "vs" in t):
        return {"intent": "revenue_vs_budget", "month": _find_single_month(text), "last_n": None}

    if ("gross margin" in t or "gm" in t) and ("trend" in t or "last" in t):
        return {"intent": "gross_margin_trend", "month": None, "last_n": _find_last_n_months(text)}

    if "opex" in t and ("breakdown" in t or "by category" in t):
        return {"intent": "opex_breakdown", "month": _find_single_month(text), "last_n": None}

    # fallback: try to guess month and map simple keywords
    if "gross margin" in t:
        return {"intent": "gross_margin_trend", "month": None, "last_n": 3}

    return {"intent": None, "month": _find_single_month(text), "last_n": None}
