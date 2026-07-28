# Use Case Diagram

## Actors and Use Cases

```
                ┌──────────────────────────────────────────────────┐
                │              AQI Prediction System               │
                │                                                  │
  ┌─────────┐   │  ┌─────────────────────────────────────────┐    │
  │ Citizen │───┼──│  Register / Login / Forgot Password      │    │
  └─────────┘   │  │  View Dashboard                         │    │
       │        │  │  Predict AQI (single)                   │    │
       │        │  │  View Health Advisory                   │    │
       │        │  │  View SHAP Explanation                  │    │
       │        │  │  Browse Historical Data                 │    │
       │        │  │  Download PDF / CSV Reports             │    │
       │        │  │  Upload Dataset (CSV/XLSX)              │    │
       │        │  │  Update Profile / Change Password       │    │
       │        │  └─────────────────────────────────────────┘    │
       │        │                                                  │
  ┌────▼──────┐ │  ┌─────────────────────────────────────────┐    │
  │Researcher │─┼──│  All Citizen use cases +                 │    │
  └───────────┘ │  │  Fetch Data from OpenAQ API             │    │
       │        │  │  View ML Model Metrics                  │    │
       │        │  │  Generate Full XAI Reports (SHAP+LIME)  │    │
       │        │  │  Batch AQI Prediction (up to 500)       │    │
       │        │  └─────────────────────────────────────────┘    │
       │        │                                                  │
  ┌────▼────────┐│  ┌─────────────────────────────────────────┐   │
  │Policy Maker ││  │  All Citizen use cases +                 │   │
  └─────────────┘│  │  View Analytics Dashboard               │   │
       │        │  │  City Comparison Charts                 │    │
       │        │  │  Trend Reports                          │    │
       │        │  └─────────────────────────────────────────┘    │
       │        │                                                  │
  ┌────▼─────┐  │  ┌─────────────────────────────────────────┐    │
  │  Admin   │──┼──│  All above use cases +                   │    │
  └──────────┘  │  │  Manage Users (activate/deactivate/role)│    │
                │  │  Manage Datasets (view/delete any)      │    │
                │  │  Manage ML Models (activate production) │    │
                │  │  View All Predictions                   │    │
                │  │  View Audit Logs                        │    │
                │  │  View System Stats                      │    │
                │  └─────────────────────────────────────────┘    │
                │                                                  │
                │  ┌──────────────────────────────────┐           │
  ┌──────────┐  │  │  External Systems                │           │
  │ OpenAQ   │──┼──│  OpenAQ API Integration          │           │
  │   API    │  │  │  Public Sensor Data Ingestion    │           │
  └──────────┘  │  └──────────────────────────────────┘           │
                └──────────────────────────────────────────────────┘
```

## Key Use Case Descriptions

### UC-01: Predict AQI
- **Actor:** Any authenticated user (or anonymous)
- **Input:** PM2.5, PM10, NO2, SO2, CO, O3 (required); weather data (optional)
- **Processing:** ML model prediction + SHAP explanation
- **Output:** AQI value, health category, advisory text, SHAP waterfall chart

### UC-02: Upload Dataset
- **Actor:** Any authenticated user
- **Input:** CSV or XLSX file (max 50 MB)
- **Processing:** Clean pipeline → AQI calculation → DB insert
- **Output:** Dataset record with row count, status

### UC-03: Download Report
- **Actor:** Any authenticated user
- **Types:** Prediction history (PDF/CSV), Analytics (PDF/CSV)
- **Output:** File download

### UC-04: Activate ML Model
- **Actor:** Admin only
- **Action:** Set a trained model as the production model
- **Effect:** All subsequent predictions use the new model

### UC-05: View Audit Logs
- **Actor:** Admin only
- **Content:** All security-relevant actions (login, CRUD, role changes)
- **Immutable:** Audit records cannot be edited or deleted
