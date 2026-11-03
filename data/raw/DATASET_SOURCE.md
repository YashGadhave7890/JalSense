# Public Water Consumption Dataset Documentation

## 1. Dataset Overview
- **Name:** Minutely Water Consumption Dataset
- **Repository / Source:** [LukaLike/water-consumption-data](https://github.com/LukaLike/water-consumption-data)
- **License:** Creative Commons Attribution-ShareAlike (CC-BY-SA)
- **Raw File:** `minutely-water-consumption-data.csv` (263,811 observations)
- **Time Period:** 2022-08-13 to 2023-03-02 (~202 continuous days)
- **Sampling Frequency:** High-frequency 1-minute meter pulse recordings

## 2. Geographic Modeling & Study Area Designation
> **Important Academic & ADS Lab Notice:**  
> Indian government municipal portals (e.g. data.gov.in, Jal Jeevan Mission dashboard, NWIC) openly publish water quality parameters (fluoride, arsenic, iron, pH) and groundwater reservoir levels, but **do not publish high-frequency household or village-level smart meter consumption telemetry** due to privacy restrictions and infrastructure rollout stages.  
>  
> To ensure **strict scientific integrity without fabricating observations**:
> - This public dataset is modeled as **Micro-Catchment Study Unit 01 (`STUDY_RES_01`)**.
> - It is **NOT** falsely labeled as an Indian rural village; it is explicitly designated as an empirical empirical consumer study area for training and validating demand time-series models.
> - The architecture is designed to be **100% plug-and-play adaptable**: when an actual Gram Panchayat or Jal Sansthan SCADA CSV is provided, placing it into `data/raw/` automatically replaces this study area without code modifications.

## 3. Data Processing & Standardization Pipeline
1. **Timestamp Conversion:** Epoch timestamp (`created_at` in integer seconds) is parsed to UTC datetime.
2. **Date Standardization:** Standardized to canonical `date` in `YYYY-MM-DD` ISO format.
3. **Target Variable Identification:** `water_consumption_litres` (daily sum of physical pulse measurements).
4. **Meteorological Augmentation:** Historical daily temperature (`temp_mean`, `temp_max`, `temp_min`), precipitation (`rainfall_mm`), and relative humidity (`humidity_pct`) were fetched from the Open-Meteo Archive API matching the study period.
5. **Output Files:**
   - Raw: `data/raw/public_water_consumption_raw.csv`
   - Clean Daily: `data/processed/public_water_consumption_daily_clean.csv`
   - Unified Features: `data/processed/unified_features.csv`
