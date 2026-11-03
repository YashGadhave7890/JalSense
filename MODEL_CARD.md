# JalSense Model Card

## 1. Model Details

- **Model Name:** JalSense Rural Water Demand & Shortage Predictor
- **Version:** `v2.0.0-champion-xgboost`
- **Model Type:** Gradient Boosted Decision Trees (`XGBoostRegressor`) & Deep Artificial Neural Network (`TensorFlow/Keras`)
- **Champion Architecture:** XGBoost (`n_estimators=100`, `max_depth=5`, `learning_rate=0.08`, `subsample=0.85`)
- **Alternative Deep Learning Architecture:** Keras Sequential ANN (Input $\rightarrow$ Dense 128 ReLU $\rightarrow$ BatchNormalization $\rightarrow$ Dropout 0.30 $\rightarrow$ Dense 64 ReLU $\rightarrow$ BatchNormalization $\rightarrow$ Dropout 0.20 $\rightarrow$ Dense 32 ReLU $\rightarrow$ Dense 1)
- **Primary Frameworks:** `xgboost 2.0.3`, `scikit-learn 1.8.0`, `tensorflow 2.21.0`, `joblib 1.3.0`
- **Release Date:** October 2026
- **License:** MIT License

---

## 2. Intended Use

### Intended Use Cases
- **Next-Day Demand Forecasting:** Estimating total volumetric water requirements (in litres and Litres Per Capita per Day - LPCD) for rural habitations and micro-catchment study units.
- **Shortage Risk Classification:** Calculating Gaussian margin deficit probabilities to categorize vulnerability into `LOW`, `MODERATE`, `HIGH`, or `CRITICAL`.
- **Decision-Support Requisitions:** Generating quantitative tanker requisition advisories for Gram Panchayat local governance before acute crises emerge.
- **Scenario Stress-Testing:** Simulating demographic surges, extreme heatwaves (+3°C to +8°C), and pump infrastructure failures.

### Out-of-Scope & Prohibited Uses
- **Statutory Legal Rationing:** Model advisories are strictly algorithmic decision-support tools and do **not** constitute legal or municipal administrative orders.
- **Urban Multi-Tier Industrial Complexes:** The feature space and per-capita benchmarks are calibrated for rural micro-catchments and the **Jal Jeevan Mission (55 LPCD)** standard.

---

## 3. Data & Preprocessing

- **Empirical Baseline:** 263,811 minutely smart-meter telemetry records from the publicly accessible `LukaLike/water-consumption-data` repository (CC BY-SA 4.0), aggregated into 195 daily chronological timesteps.
- **Meteorological Fusion:** Synchronized daily temperatures, rainfall (mm), and relative humidity from the **Open-Meteo Historical Archive API** matching catchment coordinates.
- **Feature Engineering (15 Features):**
  - Demographics: `population`
  - Weather: `temp_mean`, `rainfall_mm`, `humidity_pct`, `heat_index`
  - Calendar: `day_of_week`, `is_weekend`, `month`, `season_encoded`
  - Dynamic Lags: `demand_lag_1`, `demand_lag_2`, `demand_lag_7`
  - Rolling Windows: `rolling_mean_7d`, `rolling_std_7d`, `rolling_max_7d`
- **Splitting Strategy:** Strict chronological forward-split (70% Train: 2,565 observations, 15% Validation: 545 observations, 15% Test Holdout: 545 observations). Zero random shuffling to eliminate temporal lookahead leakage.

---

## 4. Benchmark Evaluation Results

Evaluation conducted on strictly held-out chronological test sets:

| Model Architecture | Test MAE (L) | Test RMSE (L) | Test $R^2$ Score | Test WAPE (%) | Selection Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **XGBoost Regressor** | **6,589.57** | **9,309.34** | **0.9884** | **3.46%** | 🏆 **Champion** |
| Random Forest Regressor | 6,666.00 | 9,437.59 | 0.9881 | 3.50% | Benchmark |
| TensorFlow/Keras Deep ANN | 7,679.00 | 10,195.46 | 0.9861 | 4.03% | Deep Learning |
| Linear Regression Baseline | 7,854.81 | 11,005.85 | 0.9839 | 4.12% | Baseline |

---

## 5. Shortage Risk Methodology

JalSense formulates shortage as a stochastic margin:
$$M = (S + \alpha B) - D$$
Where:
- $D \sim \mathcal{N}(\mu_D, \sigma_D^2)$: Predicted demand with model residual variance $\sigma_D$.
- $S \sim \mathcal{N}(\mu_S, \sigma_S^2)$: Available daily yield with supply pump variance $\sigma_S$.
- $B$: Storage reservoir buffer capacity (drawdown factor $\alpha = 0.50$).
- **Shortage Probability:**
$$P(\text{Shortage}) = P(M < 0) = \Phi\left(\frac{-\mu_M}{\sigma_M}\right)$$

---

## 6. Limitations & Assumptions

1. **Micro-Catchment Calibration:** Empirical observations reflect residential micro-catchment smart meters. While scalable to any village via baseline population configuration, continuous ground-truth telemetry from local SCADA/borewell flowmeters improves local convergence.
2. **Extreme Meteorological Outliers:** Cyclonic rainfall (>150mm/day) or sub-zero freezes outside the historical training envelope default to bounded conservative estimates.
3. **Pumping Variances:** Pumping supply assumes documented regional Gram Panchayat yield averages unless overridden in the Scenario Simulator.
