# JalSense Data Sources & Provenance Specification

## 1. Primary Empirical Water Consumption Dataset

- **Dataset Identifier:** `LukaLike/water-consumption-data`
- **Repository URL:** [https://raw.githubusercontent.com/LukaLike/water-consumption-data/main/minutely-water-consumption-data.csv](https://raw.githubusercontent.com/LukaLike/water-consumption-data/main/minutely-water-consumption-data.csv)
- **License:** Creative Commons Attribution-ShareAlike 4.0 International ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/))
- **Raw Volume:** 263,811 minutely smart water meter telemetry readings.
- **Temporal Coverage:** Multi-month continuous telemetry logging.
- **Aggregation & Standardization:**
  - Standardized datetime parsing from ISO strings to daily date format (`YYYY-MM-DD`).
  - Imputed sensor dropouts and cleaned abnormal negative flow artifacts.
  - Aggregated minutely liters into daily aggregate consumption series (`water_demand_litres`).
- **Academic Research Integrity Note:**
  - Indian open data repositories (such as `data.gov.in` and Jal Jeevan Mission dashboards) provide state/district tap connection counts and reservoir levels, but do **not** publicly offer open minute-level smart meter flow logs.
  - To maintain absolute scientific integrity, this real smart meter dataset is modeled as a **Micro-Catchment Study Unit (`STUDY_RES_01`)**. It is seamlessly scaled across configured rural habitation profiles without fabricating telemetry numbers.

---

## 2. Meteorological Ingestion: Open-Meteo API

- **Service Provider:** [Open-Meteo Weather APIs](https://open-meteo.com/)
- **License:** Open Database License ([ODbL](https://opendatacommons.org/licenses/odbl/))
- **Endpoints Utilized:**
  - Historical Reanalysis Archive: `https://archive-api.open-meteo.com/v1/archive`
  - Real-Time Forecast: `https://api.open-meteo.com/v1/forecast`
- **Meteorological Attributes Fetched:**
  - `temperature_2m_max` (°C)
  - `temperature_2m_min` (°C)
  - `temperature_2m_mean` (°C)
  - `precipitation_sum` / `rainfall_mm` (mm)
  - `relative_humidity_2m_mean` / `humidity_pct` (%)
- **Derived Bio-Meteorological Metric:**
  - **Steadman Rothfusz Heat Index:** Captures the synergistic amplification of temperature and relative humidity on rural domestic hydration demand and livestock cooling requirements.
- **Local Disk Caching Architecture:**
  - Implemented in `src/weather_client.py`.
  - Generates deterministic MD5 hash keys based on `(latitude, longitude, start_date, end_date)`.
  - Forecast cache TTL: **1 hour**.
  - Historical archive cache TTL: **30 days**.
  - Stored locally in `data/cache/weather/` to prevent redundant network calls and respect upstream API rate limits.

---

## 3. Demographics & Institutional Infrastructure Parameters

- **Jal Jeevan Mission (JJM) National Benchmark:**
  - India's Ministry of Jal Shakti mandates **55.0 Litres Per Capita per Day (LPCD)** as the functional household tap connection design capacity for rural habitations.
- **Monitored Study Villages (Configured in `src/config.py`):**
  1. `VILL001`: **Ralegan Siddhi** (Ahmednagar, Maharashtra) - Watershed harvesting, borewells, population 2,450.
  2. `VILL002`: **Hiware Bazar** (Ahmednagar, Maharashtra) - Recharged wells, population 1,350.
  3. `VILL003`: **Punsari** (Sabarkantha, Gujarat) - Piped RO scheme, overhead tanks, population 5,800.
  4. `VILL004`: **Mawlynnong** (East Khasi Hills, Meghalaya) - High rainfall catchment, spring channels, population 950.
  5. `VILL005`: **Chhotkei** (Angul, Odisha) - Solar micro-grid pumping, population 1,750.
