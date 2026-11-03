# JalSense Sample Benchmark Dataset

**Dataset Type:** Grounded Synthetic Benchmark (`is_synthetic_benchmark = True`)

**Compliance:** Jal Jeevan Mission (JJM) rural standard of 55 LPCD baseline.

**Purpose:** Provides a consistent, reproducible baseline for time-series feature engineering, machine learning model training, and shortage evaluation in village water management.

**Replacing with Real Data:**
Place your real meter/SCADA logs CSV into `data/raw/village_water_demand_raw.csv` with the columns:
`[date, village_id, population, temp_mean, rainfall_mm, humidity_pct, daily_supply_litres, water_demand_litres]`.
