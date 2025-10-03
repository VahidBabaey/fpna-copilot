# agent/tools/pdf_export.py
from __future__ import annotations
from io import BytesIO
from typing import Dict
import pandas as pd

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch

from agent.tools.charts import (
    bar_actual_vs_budget, pie_opex_breakdown, line_cash_trend
)
from agent.tools.metrics import (
    revenue_vs_budget, opex_breakdown_by_category
)
from agent.answer_formatter import fmt_month
import plotly.io as pio

def _plotly_fig_to_png_bytes(fig, scale=2.0, width=900, height=500) -> bytes:
    return pio.to_image(fig, format="png", width=width, height=height, scale=scale)

def build_board_pdf(data: Dict[str, pd.DataFrame], month: pd.Period) -> bytes:
    """
    Builds a compact board PDF (1–2 pages) and returns its bytes.
    Sections:
      1) Revenue vs Budget (selected month)
      2) Opex breakdown (selected month)
      3) Cash trend (last 12 months)
    """
    actuals = data["actuals_usd"]
    budget  = data["budget_usd"]
    cash    = data["cash_usd"]

    # ----- Figures -----
    # 1) Revenue vs Budget
    r = revenue_vs_budget(actuals, budget, month)
    fig_rev = bar_actual_vs_budget(str(month), r["revenue_actual_usd"], r["revenue_budget_usd"])
    png_rev = _plotly_fig_to_png_bytes(fig_rev)

    # 2) Opex breakdown
    opex_series = opex_breakdown_by_category(actuals, month)
    fig_opex = pie_opex_breakdown(opex_series, month_label=str(month))
    png_opex = _plotly_fig_to_png_bytes(fig_opex)

    # 3) Cash trend (last 12 months)
    cash_tail = cash.sort_values("month").tail(12)
    fig_cash = line_cash_trend(cash_tail, title="Cash (last 12 months)")
    png_cash = _plotly_fig_to_png_bytes(fig_cash)

    # ----- PDF assembly -----
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    W, H = LETTER
    margin = 0.6 * inch
    title_y = H - margin

    # Page 1
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, title_y, f"FP&A Snapshot — {fmt_month(month)}")

    # Revenue vs Budget
    y = title_y - 0.4*inch
    img_rev = ImageReader(BytesIO(png_rev))
    # fit image to width
    img_w = W - 2*margin
    img_h = img_w * (9/16)  # approximate aspect
    c.drawImage(img_rev, margin, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    y = y - img_h - 0.2*inch
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Revenue vs Budget for {fmt_month(month)}")

    # Opex breakdown (if space fits, else new page)
    y = y - 0.2*inch
    opex_h = img_w * (9/16)
    if y - opex_h < margin:
        c.showPage()
        y = H - margin
    img_opex = ImageReader(BytesIO(png_opex))
    c.drawImage(img_opex, margin, y - opex_h, width=img_w, height=opex_h, preserveAspectRatio=True, mask='auto')
    y = y - opex_h - 0.2*inch
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Opex breakdown — {fmt_month(month)}")

    # Cash trend (always start on a new page for clarity)
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, H - margin, "Cash Trend")
    img_cash = ImageReader(BytesIO(png_cash))
    c.drawImage(img_cash, margin, H - margin - 0.4*inch - img_h, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')

    c.save()
    buf.seek(0)
    return buf.getvalue()
