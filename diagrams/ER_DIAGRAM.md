# Entity Relationship Diagram

## Tables and Relationships

```
┌──────────────────────────────────────────────────────────────────────┐
│ roles                                                                │
│─────────────────────────────────────────────────────────────────────│
│ PK  id          TINYINT UNSIGNED  AUTO_INCREMENT                     │
│     name        VARCHAR(50)       UNIQUE  NOT NULL                   │
│     description VARCHAR(255)                                         │
│     created_at  DATETIME          DEFAULT NOW()                      │
└──────────────────────┬───────────────────────────────────────────────┘
                       │ 1
                       │
                       │ N
┌──────────────────────▼───────────────────────────────────────────────┐
│ users                                                                │
│─────────────────────────────────────────────────────────────────────│
│ PK  id                    INT UNSIGNED  AUTO_INCREMENT               │
│ FK  role_id               TINYINT  → roles.id                        │
│     email                 VARCHAR(255)  UNIQUE  NOT NULL             │
│     username              VARCHAR(100)  UNIQUE  NOT NULL             │
│     password_hash         VARCHAR(255)  NOT NULL                     │
│     first_name            VARCHAR(100)                               │
│     last_name             VARCHAR(100)                               │
│     phone                 VARCHAR(20)                                │
│     organization          VARCHAR(255)                               │
│     city                  VARCHAR(100)                               │
│     country               VARCHAR(100)                               │
│     is_active             BOOLEAN  DEFAULT TRUE                      │
│     is_verified           BOOLEAN  DEFAULT FALSE                     │
│     avatar_url            VARCHAR(512)                               │
│     last_login            DATETIME                                   │
│     password_reset_token  VARCHAR(255)                               │
│     reset_token_expires   DATETIME                                   │
│     verify_token          VARCHAR(255)                               │
│     created_at            DATETIME  DEFAULT NOW()                    │
│     updated_at            DATETIME  ON UPDATE NOW()                  │
│                                                                      │
│ Indexes: uq(email), uq(username), idx(role_id), idx(city)           │
└──────────┬──────────────────────────────────────────────────────────┘
           │ 1
   ┌───────┼────────────────────────┬───────────────────────┐
   │       │                        │                       │
   │N      │N                       │N                      │N
┌──▼───────┴──┐  ┌──────────────────▼──┐  ┌────────────────▼──┐
│refresh_tokens│  │     datasets         │  │    predictions    │
│─────────────│  │─────────────────────│  │──────────────────│
│PK id        │  │PK id                │  │PK id  BIGINT      │
│FK user_id   │  │FK user_id           │  │FK user_id         │
│   jti       │  │   name              │  │FK model_id        │
│   is_revoked│  │   source (ENUM)     │  │   city            │
│   expires_at│  │   file_path         │  │   input_features  │
│   created_at│  │   status (ENUM)     │  │   predicted_aqi   │
└─────────────┘  │   row_count         │  │   aqi_category    │
                 │   date_from / to    │  │   health_advisory │
                 │   is_public         │  │   explanation     │
                 └──────────┬──────────┘  │   ip_address      │
                            │ 1           │   requested_at    │
                            │             └───────────────────┘
                            │ N
                 ┌──────────▼──────────┐
                 │    aqi_readings      │
                 │────────────────────│
                 │PK id    BIGINT      │
                 │FK dataset_id        │
                 │   station_id        │
                 │   city              │
                 │   country           │
                 │   latitude/longitude│
                 │   recorded_at       │
                 │   pm25, pm10, no2   │
                 │   so2, co, o3, nh3  │
                 │   temperature       │
                 │   humidity          │
                 │   wind_speed/dir    │
                 │   pressure          │
                 │   aqi               │
                 │   aqi_category      │
                 └─────────────────────┘

┌─────────────────────────┐      ┌─────────────────────────┐
│       ml_models          │      │         reports          │
│─────────────────────────│      │─────────────────────────│
│PK id                    │      │PK id                    │
│   name                  │      │FK user_id               │
│   algorithm (ENUM)      │      │   title                 │
│   version               │      │   report_type (ENUM)    │
│   file_path             │      │   format (ENUM)         │
│   scaler_path           │      │   file_path             │
│   feature_names (JSON)  │  1─N │   parameters (JSON)     │
│   hyperparameters (JSON)│──────│   file_size_kb          │
│   mae / rmse / mse / r2 │      │   created_at            │
│   training_time_s       │      └─────────────────────────┘
│   is_active             │
│   trained_by → users.id │
│   trained_at            │
└────────────┬────────────┘
             │ 1
             │
             │ N
             │ (predictions.model_id → ml_models.id)

┌─────────────────────────┐
│       audit_logs         │
│─────────────────────────│
│PK id      BIGINT        │
│FK user_id               │
│   action  VARCHAR(100)  │
│   entity  VARCHAR(100)  │
│   entity_id             │
│   old_value (JSON)      │
│   new_value (JSON)      │
│   ip_address            │
│   user_agent            │
│   status (ENUM)         │
│   created_at            │
└─────────────────────────┘
```

## Cardinalities

| Relationship | Type |
|---|---|
| roles → users | 1 : N |
| users → refresh_tokens | 1 : N (cascade delete) |
| users → datasets | 1 : N (cascade delete) |
| users → predictions | 1 : N (set null on delete) |
| users → reports | 1 : N (set null on delete) |
| users → audit_logs | 1 : N (set null on delete) |
| datasets → aqi_readings | 1 : N (cascade delete) |
| ml_models → predictions | 1 : N (set null on delete) |

## Indexes

| Table | Index | Type |
|---|---|---|
| users | email | UNIQUE |
| users | username | UNIQUE |
| users | role_id | INDEX |
| refresh_tokens | jti | UNIQUE |
| aqi_readings | recorded_at | INDEX |
| aqi_readings | city | INDEX |
| aqi_readings | aqi | INDEX |
| predictions | requested_at | INDEX |
| predictions | user_id | INDEX |
| audit_logs | action | INDEX |
| audit_logs | created_at | INDEX |
