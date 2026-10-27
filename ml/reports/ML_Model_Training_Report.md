# ML Model Training & Evaluation Report
## AI-Based Air Quality Index (AQI) Prediction System

---

## 1. Overview

This report documents the full machine learning pipeline used to train, evaluate, and select the best model for predicting the Air Quality Index (AQI) from pollutant and weather sensor data. Five regression models were trained and compared using four standard metrics. The best-performing model was automatically selected and deployed to production.

---

## 2. Dataset Details

| Property | Value |
|---|---|
| **Source** | `AIR_QUALITY_WITH_AQI.xlsx` |
| **Total rows** | 87,672 |
| **Training set** | 70,137 rows (80%) |
| **Testing set** | 17,535 rows (20%) |
| **Split method** | `train_test_split` with `random_state=42` |
| **Scaling** | `StandardScaler` (fit on train, applied to test) |

### Raw Columns
`Date, Time, pm25, pm10, no2, co, so2, o3, Temperature, Humidity, Wind, Rain, AQI, AQI_category, Dominant_Pollutant`

The `Date` and `Time` columns were combined into a single `recorded_at` datetime column, from which additional time-based features were engineered.

---

## 3. Features Used (16 total)

The model uses 16 input features across three categories:

| Category | Features | Count |
|---|---|---|
| **Pollutants** | pm25, pm10, no2, so2, co, o3 | 6 |
| **Weather** | temperature, humidity, wind_speed, rain | 4 |
| **Time-derived** | hour, day_of_week, month, year, is_weekend, season | 6 |

### Feature Engineering
Time-based features were extracted from the `recorded_at` datetime column:
- `hour` — hour of the day (0–23)
- `day_of_week` — day of week (0=Monday, 6=Sunday)
- `month` — month number (1–12)
- `year` — calendar year
- `is_weekend` — binary flag (1 if Saturday/Sunday, else 0)
- `season` — numeric season mapping (0=Winter, 1=Spring, 2=Summer, 3=Autumn)

---

## 4. Models Trained

Five models were trained and evaluated. A sixth model (LSTM) is available in the code but was disabled due to TensorFlow incompatibility with Python 3.13.

### Model 1: Linear Regression
- **Library:** `sklearn.linear_model.LinearRegression`
- **Purpose:** Baseline model — assumes a linear relationship between features and target.
- **Hyperparameters:** Default (no tuning)
- **Characteristics:** Fastest to train, simplest to interpret, but cannot capture nonlinear pollutant-AQI relationships.

### Model 2: Decision Tree
- **Library:** `sklearn.tree.DecisionTreeRegressor`
- **Hyperparameters:** `max_depth=12`, `min_samples_split=10`, `random_state=42`
- **Characteristics:** Captures nonlinear relationships through recursive splitting. Prone to overfitting at high depth, controlled here with `max_depth=12`.

### Model 3: Random Forest (Best Model)
- **Library:** `sklearn.ensemble.RandomForestRegressor`
- **Hyperparameters:** `n_estimators=200`, `n_jobs=-1`, `random_state=42`
- **Characteristics:** Ensemble of 200 decision trees. Each tree is trained on a bootstrap sample, and predictions are averaged. Reduces overfitting and variance compared to a single tree. This was selected as the best model.

### Model 4: XGBoost
- **Library:** `xgboost.XGBRegressor`
- **Hyperparameters:** `n_estimators=500`, `learning_rate=0.05`, `max_depth=7`, `subsample=0.8`, `colsample_bytree=0.8`, `n_jobs=-1`, `random_state=42`
- **Characteristics:** Gradient boosting model that builds trees sequentially, each correcting errors from the previous. Uses early stopping on the validation set. Strong performer on tabular data.

### Model 5: LightGBM
- **Library:** `lightgbm.LGBMRegressor`
- **Hyperparameters:** `n_estimators=500`, `learning_rate=0.05`, `num_leaves=64`, `subsample=0.8`, `n_jobs=-1`, `random_state=42`
- **Characteristics:** Leaf-wise gradient boosting (vs. level-wise in XGBoost). Early stopping with patience=50. Typically faster than XGBoost with comparable accuracy.

### Model 6: LSTM (Disabled)
- **Library:** `tensorflow.keras`
- **Architecture:** 2-layer stacked LSTM (128 → 64 units), BatchNormalization, Dropout (0.3 → 0.2), Dense(32) → Dense(1)
- **Status:** Disabled — TensorFlow is not compatible with Python 3.13. Can be enabled with `--lstm` flag on Python 3.11.

---

## 5. Evaluation Metrics

Each model was evaluated on the held-out 20% test set using four metrics:

| Metric | Formula | Interpretation |
|---|---|---|
| **MAE** (Mean Absolute Error) | `mean(|y_true - y_pred|)` | Average magnitude of prediction errors. Lower is better. |
| **MSE** (Mean Squared Error) | `mean((y_true - y_pred)²)` | Penalizes large errors more heavily. Lower is better. |
| **RMSE** (Root Mean Squared Error) | `sqrt(MSE)` | Error in the same units as the target (AQI). Lower is better. |
| **R²** (Coefficient of Determination) | `1 - SS_res/SS_tot` | Proportion of variance explained (0–1). Higher is better. 1.0 = perfect. |

---

## 6. Results Comparison

### Full Results Table

| Model | MAE | MSE | RMSE | R² | Train Time (s) |
|---|---|---|---|---|---|
| **Random Forest** | **0.1243** | **1.4599** | **1.2083** | **0.9998** | 34.95 |
| LightGBM | 1.3235 | 30.2526 | 5.5002 | 0.9959 | 1.12 |
| XGBoost | 2.0497 | 37.0921 | 6.0903 | 0.9950 | 3.67 |
| Decision Tree | 0.6597 | 3.5978 | 1.8968 | 0.9995 | 0.61 |
| Linear Regression | 21.4970 | 909.1303 | 30.1518 | 0.8780 | 0.06 |

### Ranking (by RMSE — primary selection metric)

| Rank | Model | RMSE | R² |
|---|---|---|---|
| 1 | Random Forest | 1.2083 | 0.9998 |
| 2 | Decision Tree | 1.8968 | 0.9995 |
| 3 | LightGBM | 5.5002 | 0.9959 |
| 4 | XGBoost | 6.0903 | 0.9950 |
| 5 | Linear Regression | 30.1518 | 0.8780 |

### Generated Plots
The following comparison plots were generated and are available in `ml/reports/`:

| Plot File | Description |
|---|---|
| `model_comparison.png` | Original 3-panel comparison (MAE, RMSE, R²) |
| `11_rmse_comparison.png` | RMSE bar chart sorted best-to-worst |
| `12_r2_comparison.png` | R² score bar chart sorted best-to-worst |
| `13_training_time_comparison.png` | Training time comparison |
| `14_performance_dashboard.png` | Combined 2×2 dashboard (MAE, RMSE, R², Train Time) |
| `15_best_model_highlight.png` | Best model highlighted in red with annotations |

---

## 7. Best Model: Random Forest

### Why Random Forest Was Selected

The model with the **lowest RMSE** on the test set is automatically saved as the production model. Random Forest achieved:

- **RMSE = 1.2083** — lowest of all models (predictions are off by ~1.2 AQI units on average)
- **R² = 0.9998** — explains 99.98% of the variance in AQI (near-perfect)
- **MAE = 0.1243** — lowest absolute error

### Performance Analysis

| Model | Key Strength | Key Weakness |
|---|---|---|
| Random Forest | Best accuracy, low variance | Slowest training (34.95s) |
| LightGBM | Fastest of the boosting models (1.12s) | Higher RMSE than RF |
| XGBoost | Good generalization | Slower than LightGBM (3.67s) |
| Decision Tree | Fast training, interpretable | Single tree — higher variance |
| Linear Regression | Fastest (0.06s) | Cannot model nonlinear relationships |

### Why Not XGBoost or LightGBM?
On this dataset, Random Forest outperformed both gradient boosting methods. This is common when:
- The dataset is large enough that the ensemble averaging in RF is very effective
- The feature-target relationship is well-captured by tree splits (no need for sequential error correction)
- The data has lower noise, so RF's variance reduction through bagging is sufficient

Gradient boosting methods (XGBoost, LightGBM) typically shine on noisier datasets or when the model needs to correct systematic errors iteratively.

### Why Not Linear Regression?
Linear Regression assumes AQI is a linear function of pollutants. In reality, AQI depends on pollutant interactions and breakpoints (EPA AQI calculation uses sub-index maximum, which is nonlinear). R² = 0.878 confirms it captures the general trend but misses the fine-grained patterns that tree-based models catch.

---

## 8. Production Deployment

The best model is deployed through the following artifacts in `ml/models/`:

| File | Description |
|---|---|
| `aqi_model.pkl` | Trained Random Forest model (joblib serialized) |
| `scaler.pkl` | Fitted StandardScaler for feature normalization |
| `feature_names.json` | Ordered list of 16 feature names |
| `best_model_meta.json` | Metadata: algorithm, metrics, features |
| `model_comparison.csv` | Full comparison table for all models |

### Prediction Flow (in Production)

1. Frontend sends pollutant + weather values via `POST /api/v1/predictions/`
2. `AQIPredictor` (singleton) loads model, scaler, and feature list once on startup
3. Input features are ordered according to `feature_names.json`
4. `StandardScaler` normalizes the input vector
5. Random Forest model produces the AQI prediction
6. SHAP TreeExplainer generates feature-level explanations
7. Response includes: predicted AQI, AQI category, health advisory, and SHAP explanation

---

## 9. Explainable AI (XAI)

Every prediction is accompanied by an explanation to make the model transparent and trustworthy.

### SHAP (SHapley Additive exPlanations)
- **Method:** `TreeExplainer` for the Random Forest model (fast, exact)
- **Output:** SHAP values per feature, base value, and a waterfall bar chart (base64 PNG)
- **Interpretation:** Positive SHAP value = pollutant pushes AQI higher (red bar). Negative = pushes lower (blue bar).
- **Endpoint:** Available via `POST /api/v1/predictions/explain`

### LIME (Local Interpretable Model-Agnostic Explanations)
- **Method:** `TabularExplainer` fits a local linear model around each prediction
- **Output:** Feature weights, predicted value, intercept, fidelity score, and a bar chart
- **Endpoint:** Available via `POST /api/v1/predictions/explain` with `"methods": ["shap", "lime"]`

---

## 10. Conclusion

| Aspect | Summary |
|---|---|
| **Models trained** | 5 (Linear Regression, Decision Tree, Random Forest, XGBoost, LightGBM) |
| **Best model** | Random Forest (RMSE=1.21, R²=0.9998) |
| **Selection criterion** | Lowest RMSE on 20% held-out test set |
| **Features** | 16 (6 pollutants + 4 weather + 6 time-derived) |
| **Dataset size** | 87,672 rows (70,137 train / 17,535 test) |
| **Explainability** | SHAP + LIME for every prediction |
| **LSTM status** | Disabled (TensorFlow incompatible with Python 3.13) |

The Random Forest model provides near-perfect AQI predictions with an average error of only ~1.2 AQI units. Combined with SHAP and LIME explanations, the system delivers both accurate predictions and full transparency into which pollutants contribute most to each prediction.
