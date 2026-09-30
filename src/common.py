"""Shared paths, data loading and chart styling."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "Forecasting_Case_Study_CFCs_V4.xlsx"
OUT = ROOT / "outputs"
CHARTS = ROOT / "charts"
OUT.mkdir(exist_ok=True)
CHARTS.mkdir(exist_ok=True)

# Chart palette
BLUE = "#2F5D8A"
RED = "#C8102E"
GREY = "#8C8C8C"
LIGHT = "#D6E2EE"

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.titleweight": "bold",
    "axes.titlesize": 12,
    "font.size": 10,
})


def load_orders() -> pd.DataFrame:
    """Order-level data with parsed dates."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Place the case-study workbook at {DATA_FILE} (see data/README.md)."
        )
    df = pd.read_excel(DATA_FILE, sheet_name="CFC_Raw_Sales_Data")
    df["Order Submit Date"] = pd.to_datetime(df["Order Submit Date"])
    df["Delivery Date"] = pd.to_datetime(df["Delivery Date"])
    df["order_date"] = df["Order Submit Date"].dt.normalize()
    return df


def load_daily() -> pd.Series:
    """Daily order counts with a complete daily index."""
    df = load_orders()
    daily = df.groupby("order_date").size().rename("orders")
    full = pd.date_range(daily.index.min(), daily.index.max(), freq="D")
    daily = daily.reindex(full)
    if daily.isna().any():
        raise ValueError("Missing days in the series")
    daily.index.name = "date"
    return daily.astype(float)
