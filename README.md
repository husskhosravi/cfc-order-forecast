# FY25 Order Forecast for Customer Fulfilment Centres (CFCs)

A case study in forecasting daily, weekly and monthly online orders for a grocery retailer's Customer Fulfilment Centres. It covers FY25 (1 July 2024 to 30 June 2025) and is built from one year of order history (FY24).

## Summary

- **FY24 orders were stable.** 147,269 orders over 366 days, averaging 402 a day, varied randomly between 302 and 499. The data shows no statistically significant trend, weekly pattern or monthly pattern, and each day is independent of the day before.
- **The model shows why a simple forecast wins.** Holt-Winters exponential smoothing was compared against benchmarks in a rolling-origin backtest. The best configuration settles on a constant level, and extra seasonal or trend terms add nothing. Accuracy is 12.2% MAPE, the same as the historical-average benchmark.
- **FY25 forecast: 148,586 orders.** That is a 402-a-day baseline plus an assumed +25% uplift on 17 promotional days (FY end, Black Friday and competitor mega sales). The 80% prediction interval is 146,588 to 150,585 orders.
- **Scenarios bound the plan.** Stronger and more frequent promotions add 6,539 orders (+4.4%). A 10% market downturn from January removes 7,354 (−4.9%). A 28-day monitoring trigger tells the business when to re-base the forecast.

![FY25 daily forecast](charts/model_forecast_daily.png)

## Documents

| Document | Contents |
|---|---|
| [EDA.md](EDA.md) | Data profile, trend and seasonality tests, insights |
| [MODEL.md](MODEL.md) | Forecast model (assumptions, method, validation), FY25 forecast report and scenario analysis |
| [PRESENTATION.md](PRESENTATION.md) | Seven-slide summary for a non-technical audience |
| `outputs/` | Daily, weekly and monthly forecasts, backtest results, scenario results, Excel scenario tool |
| `charts/` | All figures used in the documents |

## Reproduce

```bash
pip install -r requirements.txt
# place the case-study workbook in data/ (see data/README.md)
python src/eda.py && python src/forecast.py && python src/scenarios.py
```

## Key results

| | FY24 actual | FY25 forecast |
|---|---|---|
| Total orders | 147,269 (366 days) | 148,586 (365 days) |
| Average orders per day | 402.4 | 407.1 |
| 80% range, total orders | – | 146,588 – 150,585 |
| Typical day (80% range) | – | 330 – 474 |
| Promotional day (expected / 80% upper) | – | 503 / 593 |

| Scenario | FY25 orders | vs base |
|---|---|---|
| Base case | 148,586 | – |
| Scenario 1: Increased promotions | 155,125 | +6,539 (+4.4%) |
| Scenario 2: Market downturn | 141,232 | −7,354 (−4.9%) |

## Assumptions and limitations

- The promotional uplift (+25%) and competitor sale dates are **planning assumptions**. FY24 data shows no measurable uplift around Black Friday or the FY end.
- No seasonality index or market trends report was supplied with the data. Seasonality was tested directly (none found), and market shifts are handled through scenarios.
- The forecast covers total CFC orders. Item-level demand, new products and site-level splits are out of scope.

## Data

The case-study workbook is not included in this repository. See [data/README.md](data/README.md) for the expected file and schema.
