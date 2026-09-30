# FY25 CFC Order Forecast – Presentation

Seven slides for a non-technical audience. Charts are in `charts/`. Speaker notes are in italics.

---

## Slide 1 – FY25 order forecast: the bottom line

**FY25: about 148,600 orders, a steady year with promotions providing the upside.**

| | FY24 actual | FY25 forecast |
|---|---|---|
| Total orders | 147,269 | **148,586** |
| Orders per day | 402 | **407** |
| Likely range (80%) | – | **146,600 – 150,600** |

- Demand in FY24 was steady, with no underlying growth or seasonal peaks.
- The FY25 increase comes from planned promotions: FY end, Black Friday and competitor sale events.
- Two what-if scenarios show a range of −4.9% to +4.4% around the base case.

*Speaker note: "One year of orders shows a very stable business. The forecast is simple on purpose, because simpler models proved more accurate here. The real planning questions are about promotions and market shifts, which we cover with scenarios."*

---

## Slide 2 – What last year's data told us

Chart: `charts/eda_daily_orders.png`

- **Steady.** Around 402 orders every day, all year.
- **Day-to-day swings.** Most days fall between 330 and 475 orders, and those swings are random.
- **No real patterns.** No busy weekday, no peak month and no growth trend. None of the apparent differences are statistically meaningful.
- **Stable mix.** 80% of orders are from consumers and 20% from businesses. Delivery types split evenly three ways. Order value (about $100) and basket size (about 21 items) barely move.
- **Promotions left no trace.** Black Friday and FY end 2023–24 show no clear lift in orders.

*Speaker note: the mix is stable, so order volume is the only number that matters for planning.*

---

## Slide 3 – How the forecast was built

Chart: `charts/model_backtest.png`

1. **Test on unseen data.** We "forecast the past": six times, we hid 30 days and checked how close each method came.
2. **Compare approaches.** A standard forecasting method (Holt-Winters) with and without weekly patterns and trend, against simple rules of thumb.
3. **Choose the simplest accurate method.** Holt-Winters with a stable level was the most accurate, at about 12% average daily error. Adding patterns did not help, because there are none to find.
4. **Add promotions on top** as clear assumptions (+25% on 17 days) that can be edited in the output file.

*Speaker note: the model shows the data is best described by a steady level. It will adjust automatically if demand shifts.*

---

## Slide 4 – FY25 forecast

Chart: `charts/model_forecast_monthly.png`

- **Monthly:** about 12,000–12,900 orders per month. February is lowest because it is shortest, and December and June are highest because of promotions.
- **Weekly:** about 2,800 orders in a regular week, and about 3,400 in the FY-end week.
- **Daily:** 402 on a regular day (330–474 on 80% of days) and about 500 on a promotional day (plan for up to about 590).
- **Annual:** 148,586 orders, most likely between 146,600 and 150,600.

*Speaker note: individual days are hard to predict, but totals are very predictable. That makes the annual and monthly numbers solid for budgeting.*

---

## Slide 5 – What if? Two scenarios

Chart: `charts/scenario_monthly.png`

| | Orders | vs base | Busiest day to plan for |
|---|---|---|---|
| Base case | 148,586 | – | ~590 |
| **More promotions:** stronger (+50%) and one extra 2-day event each month | 155,125 | **+4.4%** | ~710 |
| **Market downturn:** demand falls 10% from January | 141,232 | **−4.9%** | ~590 |

An Excel tool lets planners change these assumptions and see the results instantly.

---

## Slide 6 – Recommendations and next steps

- **Use the forecast for FY25 planning.** Budget on 148,600 orders, and staff and stock to the daily range, not the average.
- **Measure promotions.** Test the +25% assumption on the first FY25 events, then update the forecast with the measured uplift.
- **Plan peak capacity on the upper bound.** About 590 orders on promotional days, or about 710 if promotions are stepped up.
- **Watch for market shifts.** If the 28-day average moves more than about 5% (21 orders/day) from 402, re-base the forecast and adjust labour and stock.
- **Refresh monthly** as FY25 actual orders arrive.

**Challenges beyond this forecast**
- One year of history limits what can be learned about yearly cycles.
- Item-level forecasting across thousands of products, and for new products with no history, needs a different, product-attribute-based approach. This forecast sets the total volume those models work within.
- Online growth can shift demand away from nearby stores, so growth targets should consider the whole network.

---

## Slide 7 – How the order forecast is used

**Finance: budget baseline.** The FY25 total and monthly figures give a first reference point for the revenue and cost budget.

**Operations: rostering and inventory.** Daily and weekly volumes, with ranges, set labour rosters, stock levels and delivery slots at each CFC.

**Peak planning: promotional events.** Upper-bound volumes for Black Friday, FY end and competitor events make sure extra labour and capacity are in place before the peak arrives.

**Strategy: scenarios and early warning.** The scenario tool and 28-day trigger show quickly when the market is moving, so plans can change before service or cost suffers.
