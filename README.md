# FP&A Copilot — Mini CFO Assistant (Streamlit)

This app builds a small **AI-style agent** that interprets CFO questions, runs **deterministic finance functions** on monthly data from an Excel file (`actuals`, `budget`, `fx`, `cash` sheets), and returns **concise answers + charts**. Optional **PDF export** (1–2 pages) is included.

---

## What’s inside

- **Agent flow:** classify intent → run data functions → return text + chart.
- **Metrics:** Revenue vs Budget, Gross Margin %, Opex breakdown, EBITDA, Cash runway.
- **Charts:** Plotly (bar / line / pie) rendered inline in Streamlit.
- **(Optional) Export PDF:** board-ready snapshot (Revenue vs Budget, Opex breakdown, Cash trend).

---

# Repo structure

```
fpna-copilot/
├── app.py
├── agent/
├── __init__.py
├── intent_router.py        # classify query + extract month/range
├── planners.py             # map intent → metrics + chart + text
├── answer_formatter.py     # concise, board-ready sentences
├── tools/
│   ├── data_loader.py      # read xlsx, normalize months, FX→USD
│   ├── metrics.py          # revenue, cogs, opex, gm%, ebitda, runway
│   ├── charts.py           # plotly figures
│   └── finance_utils.py    # month parsing, % safety, money format
├── pdf_export.py           # (optional) 1–2 page PDF assembly
├── data/
│   └── finance.xlsx        # Excel with sheets: actuals/budget/fx/cash
├── tests/
│   ├── conftest.py
│   ├── test_intents.py
│   └── test_metrics.py
├── requirements.txt
└── README.md
```


## Quickstart (Windows + venv)

```powershell
# 1) Create & activate virtual env
python -m venv .venv
.\.venv\Scripts\Activate
python -m pip install --upgrade pip

# 2) Install deps
pip install -r requirements.txt

# 3) Place your Excel file at:
#    .\data\finance.xlsx   (sheets: actuals, budget, fx, cash)

# 4) Run the app
streamlit run app.py