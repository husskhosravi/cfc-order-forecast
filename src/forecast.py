"""Step 2 - FY25 order forecast.

Method
------
1. Compare candidate models with rolling-origin cross-validation
   (6 folds x 30-day horizons over the last 180 days of FY24).
2. Fit the selected Holt-Winters configuration on all of FY24 and forecast
   the 365 days of FY25 (1 Jul 2024 - 30 Jun 2025).
3. Apply the assumed promotional calendar as multipliers (editable in the CSV).
4. Build prediction intervals from out-of-sample errors. Weekly, monthly and
   annual intervals combine day-to-day noise with uncertainty in the level.

Run:  python src/forecast.py
Writes: outputs/forecast_daily.csv, forecast_weekly.csv, forecast_monthly.csv,
        backtest_results.csv, model_summary.json, charts/model_*.png
"""
import json
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from common import BLUE, CHARTS, GREY, LIGHT, OUT, RED, load_daily

warnings.filterwarnings("ignore")

FY25_START, FY25_END = "2024-07-01", "2025-06-30"
PROMO_UPLIFT = 1.25  # assumed +25% on promotional days (no uplift is visible in FY24 data)
Z80, Z95 = 1.2816, 1.96

# Assumed FY25 promotional calendar (brief: FY end, Black Friday, competitors' mega sales).
# Competitor dates are assumptions for planning and can be edited here or in the output CSV.
PROMO_CALENDAR = {
    "Competitor mega sale (July)": ("2024-07-16", "2024-07-17"),
    "Competitor mega sale (November)": ("2024-11-12", "2024-11-13"),
    "Black Friday to Cyber Monday": ("2024-11-29", "2024-12-02"),
    "Competitor mega sale (Boxing Day)": ("2024-12-26", "2024-12-27"),
    "End of financial year": ("2025-06-24", "2025-06-30"),
}

# ---------------------------------------------------------------- candidates

def fc_mean(train, h):
    return np.repeat(train.mean(), h)


def fc_naive(train, h):
    return np.repeat(train.iloc[-1], h)


def fc_seasonal_naive(train, h):
    last_week = train.iloc[-7:].values
    return np.resize(last_week, h)


def _hw(train, h, **kw):
    model = ExponentialSmoothing(train.values, **kw).fit(optimized=True)
    return model.forecast(h)


CANDIDATES = {
    "Historical mean (benchmark)": fc_mean,
    "Naive - last value (benchmark)": fc_naive,
    "Seasonal naive - same day last week (benchmark)": fc_seasonal_naive,
    "Holt-Winters: level only": lambda tr, h: _hw(tr, h, trend=None, seasonal=None),
    "Holt-Winters: level + weekly seasonality": lambda tr, h: _hw(
        tr, h, trend=None, seasonal="add", seasonal_periods=7),
    "Holt-Winters: level + damped trend + weekly seasonality": lambda tr, h: _hw(
        tr, h, trend="add", damped_trend=True, seasonal="add", seasonal_periods=7),
}
HW_CONFIGS = {
    "Holt-Winters: level only": dict(trend=None, seasonal=None),
    "Holt-Winters: level + weekly seasonality": dict(trend=None, seasonal="add", seasonal_periods=7),
    "Holt-Winters: level + damped trend + weekly seasonality": dict(
        trend="add", damped_trend=True, seasonal="add", seasonal_periods=7),
}


def rolling_origin_cv(y: pd.Series, folds=6, horizon=30):
    rows, errors = [], {name: [] for name in CANDIDATES}
    n = len(y)
    for f in range(folds):
        cut = n - (folds - f) * horizon
        train, test = y.iloc[:cut], y.iloc[cut:cut + horizon]
        for name, fn in CANDIDATES.items():
            pred = fn(train, horizon)
            err = test.values - pred
            errors[name].extend(err)
            rows.append({"model": name, "fold": f + 1,
                         "test_start": str(test.index[0].date()),
                         "mae": np.abs(err).mean(),
                         "mape": (np.abs(err) / test.values).mean() * 100})
    summary = []
    for name, errs in errors.items():
        e = np.array(errs)
        # rebuild actuals for MAPE over all folds
        summary.append({"model": name,
                        "mae": round(float(np.abs(e).mean()), 1),
                        "rmse": round(float(np.sqrt((e ** 2).mean())), 1),
                        "bias": round(float(e.mean()), 1)})
    fold_df = pd.DataFrame(rows)
    mape = fold_df.groupby("model")["mape"].mean()
    summ = pd.DataFrame(summary).set_index("model")
    summ["mape_pct"] = mape.round(2)
    return summ.sort_values("mape_pct"), fold_df, errors


def interval_sd(n_days: int, sigma: float, se_level: float) -> float:
    """SD of a sum of n daily outcomes: independent daily noise + shared level uncertainty."""
    return float(np.sqrt(n_days * sigma ** 2 + (n_days * se_level) ** 2))


def main() -> None:
    y = load_daily()

    # ---------- 1. Model comparison ----------
    cv, folds, errors = rolling_origin_cv(y)
    cv.to_csv(OUT / "backtest_results.csv")
    folds.round(2).to_csv(OUT / "backtest_folds.csv", index=False)
    print(cv.to_string())

    hw_only = cv[cv.index.str.startswith("Holt-Winters")]
    selected = hw_only["mape_pct"].idxmin()
    benchmark = "Historical mean (benchmark)"

    # ---------- 2. Fit on full FY24 ----------
    fit = ExponentialSmoothing(y.values, **HW_CONFIGS[selected]).fit(optimized=True)
    params = {k: (round(float(v), 4) if np.isscalar(v) and v is not None and not
                  (isinstance(v, float) and np.isnan(v)) else None)
              for k, v in fit.params.items()
              if k in ("smoothing_level", "smoothing_trend", "smoothing_seasonal", "damping_trend")}
    dates = pd.date_range(FY25_START, FY25_END, freq="D")
    base = np.round(fit.forecast(len(dates)), 1)  # round once so every output reconciles exactly

    # ---------- 3. Promotions ----------
    df = pd.DataFrame(index=dates)
    df.index.name = "date"
    df["base_forecast"] = base
    df["promo_multiplier"] = 1.0
    df["promo_type"] = ""
    df["is_promo"] = 0
    for name, (start, end) in PROMO_CALENDAR.items():
        df.loc[start:end, ["promo_multiplier", "promo_type", "is_promo"]] = [PROMO_UPLIFT, name, 1]
    df["final_forecast"] = df["base_forecast"] * df["promo_multiplier"]

    # ---------- 4. Intervals ----------
    sel_err = np.array(errors[selected])
    sigma = float(np.sqrt((sel_err ** 2).mean()))          # out-of-sample daily RMSE
    se_level = float(y.std() / np.sqrt(len(y)))             # uncertainty in the level itself
    daily_sd = interval_sd(1, sigma, se_level) * df["promo_multiplier"]
    df["lower_95"] = df["final_forecast"] - Z95 * daily_sd
    df["upper_95"] = df["final_forecast"] + Z95 * daily_sd
    df["lower_80"] = df["final_forecast"] - Z80 * daily_sd
    df["upper_80"] = df["final_forecast"] + Z80 * daily_sd
    df.round(1).to_csv(OUT / "forecast_daily.csv")

    def aggregate(freq_key, label):
        g = df.groupby(freq_key)
        out = g.agg(days=("final_forecast", "size"),
                    base_forecast=("base_forecast", "sum"),
                    promo_days=("is_promo", "sum"),
                    final_forecast=("final_forecast", "sum"))
        sd = out["days"].apply(lambda n: interval_sd(n, sigma, se_level))
        # scale by the average multiplier in the period
        sd = sd * (out["final_forecast"] / out["base_forecast"])
        out["lower_95"] = out["final_forecast"] - Z95 * sd
        out["upper_95"] = out["final_forecast"] + Z95 * sd
        out["lower_80"] = out["final_forecast"] - Z80 * sd
        out["upper_80"] = out["final_forecast"] + Z80 * sd
        out.index.name = label
        return out.round(0)

    week_start = df.index - pd.to_timedelta(df.index.dayofweek, unit="D")
    weekly = aggregate(week_start, "week_starting_monday")
    weekly.to_csv(OUT / "forecast_weekly.csv")
    monthly = aggregate(df.index.to_period("M").astype(str), "month")
    monthly.to_csv(OUT / "forecast_monthly.csv")

    annual_sd = interval_sd(len(df), sigma, se_level) * (df["final_forecast"].sum() / df["base_forecast"].sum())
    total = float(df["final_forecast"].sum())
    fy24_total = float(y.sum())

    promo = df[df["is_promo"] == 1]
    summary = {
        "selected_model": selected,
        "selection_rule": "Holt-Winters configuration with lowest cross-validated MAPE",
        "benchmark_model": benchmark,
        "cv_design": "Rolling origin, 6 folds x 30-day horizon over the last 180 days of FY24",
        "cv_selected": cv.loc[selected].to_dict(),
        "cv_benchmark": cv.loc[benchmark].to_dict(),
        "cv_seasonal_naive": cv.loc["Seasonal naive - same day last week (benchmark)"].to_dict(),
        "hw_parameters_full_fit": params,
        "daily_sigma_out_of_sample": round(sigma, 1),
        "level_standard_error": round(se_level, 2),
        "fy24": {"total_orders": int(fy24_total), "days": len(y), "avg_daily": round(float(y.mean()), 1)},
        "fy25": {
            "days": len(df),
            "baseline_daily": round(float(df["base_forecast"].mean()), 1),
            "baseline_total": round(float(df["base_forecast"].sum()), 0),
            "total_orders": round(total, 0),
            "avg_daily": round(total / len(df), 1),
            "total_80": [round(total - Z80 * annual_sd, 0), round(total + Z80 * annual_sd, 0)],
            "total_95": [round(total - Z95 * annual_sd, 0), round(total + Z95 * annual_sd, 0)],
            "change_vs_fy24_total_pct": round((total / fy24_total - 1) * 100, 2),
            "change_vs_fy24_avg_daily_pct": round((total / len(df) / y.mean() - 1) * 100, 2),
            "regular_day_80_range": [round(float(df.loc[df.is_promo == 0, "lower_80"].mean()), 0),
                                     round(float(df.loc[df.is_promo == 0, "upper_80"].mean()), 0)],
            "regular_day_95_range": [round(float(df.loc[df.is_promo == 0, "lower_95"].mean()), 0),
                                     round(float(df.loc[df.is_promo == 0, "upper_95"].mean()), 0)],
            "promo_day_expected": round(float(promo["final_forecast"].mean()), 0),
            "promo_day_upper_95": round(float(promo["upper_95"].mean()), 0),
            "promo_day_upper_80": round(float(promo["upper_80"].mean()), 0),
        },
        "promotions": {
            "uplift_assumed_pct": round((PROMO_UPLIFT - 1) * 100, 0),
            "promo_days": int(df["is_promo"].sum()),
            "incremental_orders": round(float((df["final_forecast"] - df["base_forecast"]).sum()), 0),
            "events": {name: {"start": s, "end": e,
                              "days": int((pd.Timestamp(e) - pd.Timestamp(s)).days + 1),
                              "incremental_orders": round(float(
                                  (df.loc[s:e, "final_forecast"] - df.loc[s:e, "base_forecast"]).sum()), 0)}
                       for name, (s, e) in PROMO_CALENDAR.items()},
        },
        "monitoring_trigger": {
            "window_days": 28,
            "threshold_orders_per_day": round(2 * sigma / np.sqrt(28), 1),
            "threshold_pct": round(2 * sigma / np.sqrt(28) / float(df["base_forecast"].mean()) * 100, 1),
        },
    }
    (OUT / "model_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in ("selected_model", "cv_selected", "cv_benchmark",
                                               "hw_parameters_full_fit", "fy25", "promotions",
                                               "monitoring_trigger")}, indent=2))

    # ---------- Charts ----------
    # Backtest comparison
    fig, ax = plt.subplots(figsize=(9, 3.8))
    order = cv.sort_values("mape_pct", ascending=False)
    colours = [RED if m == selected else (BLUE if "mean" in m else GREY) for m in order.index]
    ax.barh(order.index, order["mape_pct"], color=colours)
    for i, v in enumerate(order["mape_pct"]):
        ax.text(v + 0.2, i, f"{v:.1f}%", va="center")
    ax.set_xlabel("Cross-validated MAPE (%) - lower is better")
    ax.set_title("Model comparison: rolling-origin backtest (6 x 30 days)")
    ax.set_xlim(0, order["mape_pct"].max() * 1.15)
    fig.savefig(CHARTS / "model_backtest.png")
    plt.close(fig)

    # History + forecast
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.plot(y.index, y.values, color=GREY, lw=0.8, alpha=0.7, label="FY24 actual")
    ax.fill_between(df.index, df["lower_80"], df["upper_80"], color=LIGHT, label="80% prediction interval")
    ax.plot(df.index, df["final_forecast"], color=BLUE, lw=1.8, label="FY25 forecast")
    ax.scatter(promo.index, promo["final_forecast"], color=RED, s=14, zorder=5, label="Assumed promotion days")
    ax.set_title("FY24 actuals and FY25 daily forecast")
    ax.set_ylabel("Orders per day")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, frameon=False)
    fig.savefig(CHARTS / "model_forecast_daily.png")
    plt.close(fig)

    # Monthly forecast
    fig, ax = plt.subplots(figsize=(10, 4))
    labels = pd.to_datetime(monthly.index).strftime("%b %y")
    err = [monthly["final_forecast"] - monthly["lower_80"], monthly["upper_80"] - monthly["final_forecast"]]
    ax.bar(labels, monthly["final_forecast"], yerr=err, capsize=4, color=BLUE)
    for i, v in enumerate(monthly["final_forecast"]):
        ax.text(i, v * 0.5, f"{v/1000:.1f}K", ha="center", color="white", fontsize=9, fontweight="bold")
    ax.set_title("FY25 monthly order forecast (bars show 80% prediction interval)")
    ax.set_ylabel("Orders per month")
    fig.savefig(CHARTS / "model_forecast_monthly.png")
    plt.close(fig)


if __name__ == "__main__":
    main()
