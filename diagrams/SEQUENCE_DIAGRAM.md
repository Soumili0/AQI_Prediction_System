# Sequence Diagrams

## SD-01: User Login Flow

```
Browser          Flask API         DB (MySQL)
   │                  │                 │
   │─ POST /auth/login─►                │
   │   {email, pw}    │                 │
   │                  │─ User.query ───►│
   │                  │◄─ user record ──│
   │                  │                 │
   │                  │─ bcrypt.check() │
   │                  │  (password)     │
   │                  │                 │
   │                  │─ INSERT refresh_token ──►│
   │                  │◄─────────────────────────│
   │                  │                 │
   │                  │─ audit_log.insert ──────►│
   │◄─ 200 {access_token, refresh_token, user} ──│
```

---

## SD-02: AQI Prediction with XAI

```
Browser     Flask Route    PredictionService    AQIPredictor    SHAP Explainer    DB
   │              │                │                  │                │           │
   │─POST /predictions/────────────►                  │                │           │
   │              │─validate_input─►                  │                │           │
   │              │─enrich_time_features               │                │           │
   │              │─predict_aqi()─►                   │                │           │
   │              │                │─get_predictor()──►               │           │
   │              │                │  (singleton)      │               │           │
   │              │                │─scaler.transform()►              │           │
   │              │                │─model.predict()──►               │           │
   │              │                │◄─ aqi_float ──────│               │           │
   │              │                │─get_aqi_category()│               │           │
   │              │                │─explain_shap()────────────────────►           │
   │              │                │  TreeExplainer.shap_values()      │           │
   │              │                │  _generate_waterfall_plot()       │           │
   │              │                │◄─ {shap_values, plot_b64} ────────│           │
   │              │                │─ db.session.add(Prediction) ──────────────────►
   │              │                │◄──────────────────────────────────────────────│
   │◄─ 200 {predicted_aqi, category, advisory, explanation} ──────────────────────│
```

---

## SD-03: Dataset Upload and Cleaning

```
Browser       Dataset Route    DatasetService       DB
   │                │                │               │
   │─POST /datasets/upload ──────────►               │
   │   multipart/file                │               │
   │                │─ save file ────►               │
   │                │─ Dataset.insert(status=processing)─►
   │                │◄────────────────────────────────│
   │                │─ pd.read_csv() │               │
   │                │─ clean_dataframe()              │
   │                │  (aliases, dedup, outliers,     │
   │                │   impute, AQI calc, features)   │
   │                │─ _bulk_insert_readings()────────►
   │                │─ Dataset.update(status=ready) ──►
   │◄─ 201 {dataset metadata} ────────────────────────│
```

---

## SD-04: Admin — Activate ML Model

```
Admin Browser   Admin Route   AdminService   AQIPredictor   DB
      │               │             │               │         │
      │─PUT /admin/models/{id}/activate ────────────►         │
      │               │─ jwt_required()             │         │
      │               │─ admin_required()           │         │
      │               │─ MLModel.query.update(is_active=False) ►
      │               │─ model.is_active = True ────────────────►
      │               │─ reset_predictor() ─────────►         │
      │               │  (_MODEL_INSTANCE = None)   │         │
      │               │─ audit_log.insert ───────────────────────►
      │◄─ 200 {message: "Model X is now active"} ─────────────│
      │               │             │               │         │
   [next request]     │             │               │         │
      │─ POST /predictions/ ────────►               │         │
      │               │             │─get_predictor()─────────►
      │               │             │  loads new model.pkl    │
```

---

## SD-05: Password Reset

```
Browser        Auth Route       AuthService     DB        Email Service
   │               │                │            │              │
   │─POST /auth/forgot-password ────►            │              │
   │  {email}      │                │            │              │
   │               │─ User.query ───────────────►              │
   │               │◄──────────────────────────────────────────│
   │               │─ secrets.token_urlsafe()    │              │
   │               │─ user.password_reset_token ─►              │
   │               │─ user.reset_token_expires ──►              │
   │               │─ send_password_reset_email() ──────────────►
   │◄─ 200 {message} (always, prevents enumeration)             │
   │               │                │            │              │
   │─POST /auth/reset-password ──────►           │              │
   │  {token, new_password}          │           │              │
   │               │─ User.query(token) ─────────►              │
   │               │─ user.set_password(new_pw) ─►              │
   │               │─ RefreshToken.revoke_all ───►              │
   │◄─ 200 {message: "Password reset successfully"} ───────────│
```
