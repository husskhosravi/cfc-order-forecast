# Data

This repository does not include the case-study data. To reproduce the results, save the workbook as:

```
data/Forecasting_Case_Study_CFCs_V4.xlsx
```

Expected sheet: `CFC_Raw_Sales_Data`, one row per order (FY24: 1 Jul 2023 – 30 Jun 2024).

| Column | Type | Description |
|---|---|---|
| Order ID | integer | Order identifier (not unique, see EDA.md) |
| Order Submit Date | date | Date the order was placed |
| Delivery Date | datetime | Delivery date and time |
| Sales (AUD) | float | Order value |
| Customer ID | integer | Customer identifier |
| Customer Type | text | B2C or B2B |
| Service Type | text | Home, Unattended or Partner Delivery |
| Units | integer | Items in the order |
