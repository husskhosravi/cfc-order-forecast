"""Step 1 - Exploratory data analysis of FY24 CFC orders.

Run:  python src/eda.py
Writes: outputs/eda_summary.json, outputs/fy24_daily_orders.csv, charts/eda_*.png
"""
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from common import BLUE, CHARTS, GREY, LIGHT, OUT, RED, load_daily, load_orders

DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
FY_MONTHS = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6]
MONTH_NAMES = {m: pd.Timestamp(2024, m, 1).strftime("%b") for m in range(1, 13)}


def mean_ci(values: np.ndarray) -> tuple[float, float]:
    """Mean and 95% confidence half-width."""
    m = values.mean()
    half = stats.t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
    return m, half


def main() -> None:
    orders = load_orders()
    daily = load_daily()
    daily.to_frame().to_csv(OUT / "fy24_daily_orders.csv")

    # ---------- Data profile ----------
    lead_hours = (orders["Delivery Date"] - orders["Order Submit Date"]).dt.total_seconds() / 3600
    seg = orders.groupby("Customer Type").agg(orders=("Order ID", "count"),
                                              sales=("Sales (AUD)", "sum"),
                                              aov=("Sales (AUD)", "mean"),
                                              units=("Units", "mean"))
    svc = orders["Service Type"].value_counts(normalize=True)
    svc_by_seg = pd.crosstab(orders["Customer Type"], orders["Service Type"], normalize="index")

    profile = {
        "rows": int(len(orders)),
        "missing_values": int(orders.isna().sum().sum()),
        "duplicate_order_ids": int(orders["Order ID"].duplicated().sum()),
        "date_from": str(daily.index.min().date()),
        "date_to": str(daily.index.max().date()),
        "days": int(len(daily)),
        "total_sales_aud": round(float(orders["Sales (AUD)"].sum()), 2),
        "total_units": int(orders["Units"].sum()),
        "unique_customers": int(orders["Customer ID"].nunique()),
        "aov_mean": round(float(orders["Sales (AUD)"].mean()), 2),
        "aov_min": round(float(orders["Sales (AUD)"].min()), 2),
        "aov_max": round(float(orders["Sales (AUD)"].max()), 2),
        "units_mean": round(float(orders["Units"].mean()), 1),
        "units_min": int(orders["Units"].min()),
        "units_max": int(orders["Units"].max()),
        "lead_time_hours_median": round(float(lead_hours.median()), 1),
        "lead_time_hours_mean": round(float(lead_hours.mean()), 1),
        "lead_time_hours_min": round(float(lead_hours.min()), 1),
        "lead_time_hours_max": round(float(lead_hours.max()), 1),
        "segments": {k: {"orders": int(v.orders), "share": round(v.orders / len(orders), 3),
                         "sales_aud": round(float(v.sales), 0), "aov": round(float(v.aov), 2),
                         "units_per_order": round(float(v.units), 1)}
                     for k, v in seg.iterrows()},
        "service_share": {k: round(float(v), 3) for k, v in svc.items()},
        "service_share_by_segment": {seg_: {k: round(float(v), 3) for k, v in row.items()}
                                     for seg_, row in svc_by_seg.iterrows()},
    }

    # ---------- Daily series ----------
    series = {
        "mean": round(float(daily.mean()), 1),
        "median": float(daily.median()),
        "std": round(float(daily.std()), 1),
        "min": int(daily.min()),
        "max": int(daily.max()),
        "cv": round(float(daily.std() / daily.mean()), 3),
        "min_date": str(daily.idxmin().date()),
        "max_date": str(daily.idxmax().date()),
    }

    # ---------- Weekly pattern (per-day averages, not totals) ----------
    dow_groups = [daily[daily.index.dayofweek == i].values for i in range(7)]
    dow_stats = {}
    for i, g in enumerate(dow_groups):
        m, h = mean_ci(g)
        dow_stats[DOW[i]] = {"days": len(g), "mean": round(m, 1), "ci95": round(h, 1),
                             "index": round(m / daily.mean(), 3)}
    dow_anova = stats.f_oneway(*dow_groups)

    # ---------- Monthly pattern (per-day averages remove days-in-month effect) ----------
    month_stats = {}
    month_groups = []
    for mth in FY_MONTHS:
        g = daily[daily.index.month == mth].values
        month_groups.append(g)
        m, h = mean_ci(g)
        month_stats[MONTH_NAMES[mth]] = {"days": len(g), "total": int(g.sum()), "mean": round(m, 1),
                                         "ci95": round(h, 1), "index": round(m / daily.mean(), 3)}
    month_anova = stats.f_oneway(*month_groups)

    # ---------- Trend, autocorrelation, distribution ----------
    t = np.arange(len(daily))
    reg = stats.linregress(t, daily.values)
    first30, last30 = daily.iloc[:30].mean(), daily.iloc[-30:].mean()
    h1, h2 = daily.iloc[:183], daily.iloc[183:]
    ks_uniform = stats.kstest(daily.values, "uniform", args=(daily.min(), daily.max() - daily.min()))
    acf = {f"lag_{k}": round(float(daily.autocorr(k)), 3) for k in (1, 7, 14, 30)}
    lb_n = len(daily)
    # 95% band for autocorrelation of white noise
    acf_band = round(1.96 / np.sqrt(lb_n), 3)

    # ---------- Historical promotional windows (brief: FY end, Black Friday) ----------
    promo_windows = {
        "Black Friday weekend 2023 (24-27 Nov)": daily.loc["2023-11-24":"2023-11-27"],
        "FY end 2024 (24-30 Jun)": daily.loc["2024-06-24":"2024-06-30"],
    }
    promo_check = {k: {"mean": round(float(v.mean()), 1),
                       "vs_overall_pct": round(float(v.mean() / daily.mean() - 1) * 100, 1),
                       "values": [int(x) for x in v.values]} for k, v in promo_windows.items()}

    tests = {
        "day_of_week_anova_p": round(float(dow_anova.pvalue), 3),
        "month_anova_p": round(float(month_anova.pvalue), 3),
        "trend_slope_orders_per_day": round(float(reg.slope), 4),
        "trend_slope_p": round(float(reg.pvalue), 3),
        "trend_implied_change_over_year": round(float(reg.slope * 365), 1),
        "first_30_days_mean": round(float(first30), 1),
        "last_30_days_mean": round(float(last30), 1),
        "h1_mean": round(float(h1.mean()), 1),
        "h2_mean": round(float(h2.mean()), 1),
        "h1_vs_h2_ttest_p": round(float(stats.ttest_ind(h1, h2).pvalue), 3),
        "autocorrelation": acf,
        "autocorrelation_95pct_band": acf_band,
        "ks_uniform_p": round(float(ks_uniform.pvalue), 3),
    }

    summary = {"profile": profile, "daily_series": series, "day_of_week": dow_stats,
               "month": month_stats, "tests": tests, "historical_promo_windows": promo_check}
    (OUT / "eda_summary.json").write_text(json.dumps(summary, indent=2))

    # ---------- Charts ----------
    # 1. Daily orders with 28-day rolling mean
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(daily.index, daily.values, color=LIGHT, lw=1, label="Daily orders")
    ax.plot(daily.index, daily.rolling(28, center=True).mean(), color=BLUE, lw=2.2,
            label="28-day rolling average")
    ax.axhline(daily.mean(), color=RED, ls="--", lw=1.2, label=f"FY24 average ({daily.mean():.0f})")
    ax.set_title("FY24 daily orders: stable level, no visible trend")
    ax.set_ylabel("Orders per day")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False)
    fig.savefig(CHARTS / "eda_daily_orders.png")
    plt.close(fig)

    # 2. Day of week with 95% CI
    fig, ax = plt.subplots(figsize=(7, 4))
    means = [dow_stats[d]["mean"] for d in DOW]
    cis = [dow_stats[d]["ci95"] for d in DOW]
    ax.bar(DOW, means, yerr=cis, color=BLUE, capsize=4, alpha=0.9)
    ax.axhline(daily.mean(), color=RED, ls="--", lw=1.2)
    ax.set_ylim(350, 450)
    ax.set_title(f"Average orders by weekday (95% CI) - ANOVA p = {dow_anova.pvalue:.2f}")
    ax.set_ylabel("Average orders per day")
    fig.savefig(CHARTS / "eda_day_of_week.png")
    plt.close(fig)

    # 3. Month (per-day) with 95% CI
    fig, ax = plt.subplots(figsize=(9, 4))
    labels = list(month_stats)
    ax.bar(labels, [month_stats[m]["mean"] for m in labels],
           yerr=[month_stats[m]["ci95"] for m in labels], color=BLUE, capsize=4, alpha=0.9)
    ax.axhline(daily.mean(), color=RED, ls="--", lw=1.2)
    ax.set_ylim(350, 450)
    ax.set_title(f"Average orders per day by month (95% CI) - ANOVA p = {month_anova.pvalue:.2f}")
    ax.set_ylabel("Average orders per day")
    fig.savefig(CHARTS / "eda_month.png")
    plt.close(fig)

    # 4. Distribution
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(daily.values, bins=20, color=BLUE, alpha=0.9, edgecolor="white")
    ax.set_title("Distribution of daily orders (flat between ~300 and ~500)")
    ax.set_xlabel("Orders per day")
    ax.set_ylabel("Number of days")
    fig.savefig(CHARTS / "eda_distribution.png")
    plt.close(fig)

    # 5. Segment mix
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    seg_share = orders["Customer Type"].value_counts(normalize=True)
    axes[0].barh(seg_share.index, seg_share.values * 100, color=[BLUE, GREY])
    axes[0].set_title("Orders by customer type (%)")
    svc_pct = svc.sort_values() * 100
    axes[1].barh(svc_pct.index, svc_pct.values, color=BLUE)
    axes[1].set_title("Orders by service type (%)")
    for a in axes:
        a.set_xlim(0, 100)
    fig.savefig(CHARTS / "eda_mix.png")
    plt.close(fig)

    print(json.dumps({"daily_series": series, "tests": tests,
                      "historical_promo_windows": {k: v["vs_overall_pct"] for k, v in promo_check.items()}},
                     indent=2))


if __name__ == "__main__":
    main()
