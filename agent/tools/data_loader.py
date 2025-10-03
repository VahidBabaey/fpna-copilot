# agent/tools/data_loader.py
from __future__ import annotations
import pandas as pd
from pathlib import Path
from .finance_utils import normalize_month_column

REQUIRED_SHEETS = ["actuals", "budget", "fx", "cash"]

class DataLoadError(Exception):
    pass

def _require_sheets(xlsx: Path, xl: pd.ExcelFile) -> None:
    missing = [s for s in REQUIRED_SHEETS if s not in xl.sheet_names]
    if missing:
        raise DataLoadError(f"Missing sheet(s) in {xlsx.name}: {', '.join(missing)}")

def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def _project_usd(pl_df: pd.DataFrame, fx_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join P&L (actuals or budget) with FX on (month, currency) and compute amount_usd.
    Expects columns: month, entity, account_category, amount, currency
    FX expects columns: month, currency, rate_to_usd
    """
    required = {"month", "entity", "account_category", "amount", "currency"}
    if not required.issubset(pl_df.columns):
        raise DataLoadError(f"P&L missing columns: {required - set(pl_df.columns)}")

    if not {"month", "currency", "rate_to_usd"}.issubset(fx_df.columns):
        raise DataLoadError("FX missing required columns: month, currency, rate_to_usd")

    pl = pl_df.copy()
    fx = fx_df.copy()

    # normalize
    pl["currency"] = pl["currency"].astype(str).str.upper()
    fx["currency"] = fx["currency"].astype(str).str.upper()

    pl = normalize_month_column(pl, "month")
    fx = normalize_month_column(fx, "month")

    # join
    merged = pl.merge(fx[["month", "currency", "rate_to_usd"]],
                      on=["month", "currency"], how="left", validate="many_to_one")

    # detect missing rates
    missing_rates = merged["rate_to_usd"].isna()
    if missing_rates.any():
        bad = merged.loc[missing_rates, ["month", "currency"]].drop_duplicates()
        sample = bad.head(5).to_dict("records")
        raise DataLoadError(f"Missing FX rate_to_usd for some (month,currency). Examples: {sample}")

    merged["amount_usd"] = merged["amount"].astype(float) * merged["rate_to_usd"].astype(float)

    # standard projection
    out = merged[["month", "entity", "account_category", "amount_usd"]].copy()
    return out

def load_finance_data(xlsx_path: str | Path) -> dict[str, pd.DataFrame]:
    """
    Returns dict with:
      - actuals_usd: month, entity, account_category, amount_usd
      - budget_usd:  month, entity, account_category, amount_usd
      - cash_usd:    month, cash_usd
      - fx:          month, currency, rate_to_usd
    """
    xlsx = Path(xlsx_path)
    if not xlsx.exists():
        raise DataLoadError(f"File not found: {xlsx}")

    xl = pd.ExcelFile(xlsx)
    _require_sheets(xlsx, xl)

    # read & clean
    actuals = _clean_columns(pd.read_excel(xl, sheet_name="actuals"))
    budget  = _clean_columns(pd.read_excel(xl, sheet_name="budget"))
    fx      = _clean_columns(pd.read_excel(xl, sheet_name="fx"))
    cash    = _clean_columns(pd.read_excel(xl, sheet_name="cash"))

    # normalize month columns where present
    fx = normalize_month_column(fx, "month")
    cash = normalize_month_column(cash, "month")

    # project to USD
    actuals_usd = _project_usd(actuals, fx)
    budget_usd  = _project_usd(budget, fx)

    # ensure cash_usd shape: month, cash_usd
    if not {"month", "cash_usd"}.issubset(cash.columns):
        raise DataLoadError("cash sheet must have columns: month, cash_usd")
    cash_usd = cash[["month", "cash_usd"]].copy()

    return {
        "actuals_usd": actuals_usd,
        "budget_usd": budget_usd,
        "cash_usd": cash_usd,
        "fx": fx[["month", "currency", "rate_to_usd"]].copy(),
    }
