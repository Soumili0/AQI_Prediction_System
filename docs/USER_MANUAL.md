# User Manual — AI AQI Prediction System

## Getting Started

### 1. Create an Account
- Open the app and click **Get Started** or **Create Account**
- Fill in your name, username, email, and a strong password
- Choose your role: **Citizen**, **Researcher**, or **Policy Maker**
- Click **Create Account** — you will receive a verification email
- Click the link in the email to activate your account

### 2. Log In
- Go to the **Sign In** page
- Enter your email and password
- You will be redirected to the **Dashboard**

---

## Dashboard

The dashboard shows a real-time overview of air quality:

| Section | What it shows |
|---|---|
| Current AQI card | Latest AQI value with colour ring and health category |
| AQI Trend chart | 30-day line chart of mean and max AQI |
| Category Pie chart | Breakdown of Good / Moderate / Unhealthy readings |
| Pollutant Bar chart | Average concentration of PM2.5, PM10, NO₂, SO₂, CO, O₃ |
| Recent Predictions | Your last 5 AQI predictions |
| Quick Actions | Shortcuts to Predict, Analytics, History, Reports |

**Filter by city** using the dropdown in the top-right of the dashboard.

---

## Predict AQI

1. Click **Predict AQI** in the sidebar
2. Enter pollutant values (PM2.5, PM10, NO₂, SO₂, CO, O₃ are required)
3. Optionally add weather data and a city name
4. Click **🎯 Predict AQI**

**Results panel shows:**
- Predicted AQI value (colour-coded)
- Health category badge
- Health advisory text
- **SHAP waterfall chart** — which pollutants drove the AQI up or down
- Top 8 feature contributions as a bar chart

Click **Reset** to clear the form and result.

---

## Analytics

Interactive charts with filters:

- **City filter** — focus on one city or view all
- **Granularity** — switch between Daily / Monthly / Yearly trends
- **Period** — 30, 90, 180 days, or 1 year

Charts available:
| Chart | Description |
|---|---|
| AQI Trend (Area) | Mean + max AQI over selected period |
| City Comparison | Horizontal bar chart ranked by mean AQI |
| Pollutant Concentrations | Average of each pollutant |
| City AQI Radar | Radar comparing up to 6 cities |
| ML Model Comparison | MAE, RMSE, R² for each trained model |

---

## History

Browse the full historical readings database:

- Filter by **city** and **date range**
- Paginated table showing all pollutant values, temperature, humidity, AQI, category
- Up to 200 rows per page

---

## Reports

Download data as **PDF** or **CSV**:

| Report | Contents |
|---|---|
| Prediction History | All your prediction requests with inputs and results |
| Analytics Report | City overview, pollutant averages, category breakdown |

**Steps:**
1. Go to **Reports** in the sidebar
2. Optionally set a city filter and period (days)
3. Click **Download PDF** or **Download CSV** for the desired report

---

## Profile & Settings

### Profile
- View and edit your name, username, city, country, organization
- Change your password (requires current password)
- See your account verification status and role

### Settings
- Configure notification preferences
- Set your default city for the dashboard
- View your API access token for programmatic use

---

## AQI Health Scale Reference

| AQI | Category | Who is affected |
|---|---|---|
| 0–50 | **Good** 🟢 | Air quality is satisfactory |
| 51–100 | **Moderate** 🟡 | Acceptable; very sensitive people may be affected |
| 101–150 | **Unhealthy for Sensitive Groups** 🟠 | Heart/lung patients, elderly, children |
| 151–200 | **Unhealthy** 🔴 | Everyone may experience effects |
| 201–300 | **Very Unhealthy** 🟣 | Health alert for everyone |
| 301–500 | **Hazardous** 🔴 | Emergency conditions |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Model not trained yet" error | Run `python ml/scripts/train_models.py --no-lstm` then activate the model in Admin → Models |
| Prediction returns 503 | The ML model file is missing. See above. |
| Email verification not received | Check spam folder; contact your admin to manually verify |
| Login says "Account deactivated" | Contact your system administrator |
| Charts show "No data available" | Upload a dataset via Admin → Datasets or use the OpenAQ fetch feature |

---

## Roles Quick Reference

| Feature | Citizen | Researcher | Policy Maker | Admin |
|---|---|---|---|---|
| AQI Prediction | ✅ | ✅ | ✅ | ✅ |
| Analytics & Charts | ✅ | ✅ | ✅ | ✅ |
| Download Reports | ✅ | ✅ | ✅ | ✅ |
| Upload Datasets | ✅ | ✅ | ✅ | ✅ |
| OpenAQ API Fetch | — | ✅ | — | ✅ |
| Admin Panel | — | — | — | ✅ |
