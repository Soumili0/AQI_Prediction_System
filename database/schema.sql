-- =============================================================================
-- AI-Based AQI Prediction System — MySQL Database Schema
-- =============================================================================
-- Database: aqi_prediction_db
-- Charset : utf8mb4 (full Unicode including emoji)
-- Engine  : InnoDB (ACID transactions, FK support)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS aqi_prediction_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE aqi_prediction_db;

-- -----------------------------------------------------------------------------
-- TABLE: roles
-- Defines the four application roles.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id          TINYINT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name        VARCHAR(50)         NOT NULL,
    description VARCHAR(255)        NULL,
    created_at  DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_roles_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed roles
INSERT IGNORE INTO roles (name, description) VALUES
    ('admin',         'Full system access; manages users, models, and audit logs'),
    ('researcher',    'Access to datasets, notebooks, model training, and XAI reports'),
    ('policy_maker',  'Read-only analytics, reports, and prediction history'),
    ('citizen',       'Public-facing prediction and health advisory features');

-- -----------------------------------------------------------------------------
-- TABLE: users
-- Stores registered users with hashed passwords and role assignment.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                  INT UNSIGNED        NOT NULL AUTO_INCREMENT,
    role_id             TINYINT UNSIGNED    NOT NULL DEFAULT 4,          -- citizen
    email               VARCHAR(255)        NOT NULL,
    username            VARCHAR(100)        NOT NULL,
    password_hash       VARCHAR(255)        NOT NULL,
    first_name          VARCHAR(100)        NULL,
    last_name           VARCHAR(100)        NULL,
    phone               VARCHAR(20)         NULL,
    organization        VARCHAR(255)        NULL,
    city                VARCHAR(100)        NULL,
    country             VARCHAR(100)        NULL,
    is_active           BOOLEAN             NOT NULL DEFAULT TRUE,
    is_verified         BOOLEAN             NOT NULL DEFAULT FALSE,
    avatar_url          VARCHAR(512)        NULL,
    last_login          DATETIME            NULL,
    password_reset_token VARCHAR(255)       NULL,
    reset_token_expires  DATETIME           NULL,
    verify_token        VARCHAR(255)        NULL,
    created_at          DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email    (email),
    UNIQUE KEY uq_users_username (username),
    KEY idx_users_role_id        (role_id),
    KEY idx_users_city           (city),
    KEY idx_users_created_at     (created_at),
    CONSTRAINT fk_users_role FOREIGN KEY (role_id)
        REFERENCES roles (id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- TABLE: refresh_tokens
-- Tracks issued refresh tokens for revocation support.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED    NOT NULL,
    jti         VARCHAR(36)     NOT NULL,      -- JWT ID (UUID)
    is_revoked  BOOLEAN         NOT NULL DEFAULT FALSE,
    expires_at  DATETIME        NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_refresh_tokens_jti (jti),
    KEY idx_refresh_user_id (user_id),
    CONSTRAINT fk_refresh_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- TABLE: datasets
-- Tracks uploaded or API-fetched datasets.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS datasets (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED    NOT NULL,
    name            VARCHAR(255)    NOT NULL,
    source          ENUM(
                        'csv_upload',
                        'openaq_api',
                        'government',
                        'historical'
                    )               NOT NULL DEFAULT 'csv_upload',
    file_path       VARCHAR(512)    NULL,
    original_filename VARCHAR(255)  NULL,
    file_size_kb    INT UNSIGNED    NULL,
    row_count       INT UNSIGNED    NULL,
    column_count    SMALLINT        NULL,
    status          ENUM(
                        'pending',
                        'processing',
                        'ready',
                        'failed'
                    )               NOT NULL DEFAULT 'pending',
    processing_log  TEXT            NULL,
    date_from       DATE            NULL,
    date_to         DATE            NULL,
    location        VARCHAR(255)    NULL,
    description     TEXT            NULL,
    is_public       BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_datasets_user_id    (user_id),
    KEY idx_datasets_status     (status),
    KEY idx_datasets_created_at (created_at),
    CONSTRAINT fk_datasets_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- TABLE: aqi_readings
-- Stores raw and processed air quality readings.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aqi_readings (
    id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    dataset_id      INT UNSIGNED    NULL,
    station_id      VARCHAR(100)    NULL,
    city            VARCHAR(100)    NOT NULL,
    country         VARCHAR(100)    NULL,
    latitude        DECIMAL(9,6)    NULL,
    longitude       DECIMAL(9,6)    NULL,
    recorded_at     DATETIME        NOT NULL,
    pm25            FLOAT           NULL  COMMENT 'PM2.5 µg/m³',
    pm10            FLOAT           NULL  COMMENT 'PM10 µg/m³',
    no2             FLOAT           NULL  COMMENT 'NO₂ µg/m³',
    so2             FLOAT           NULL  COMMENT 'SO₂ µg/m³',
    co              FLOAT           NULL  COMMENT 'CO mg/m³',
    o3              FLOAT           NULL  COMMENT 'Ozone µg/m³',
    nh3             FLOAT           NULL  COMMENT 'NH₃ µg/m³',
    temperature     FLOAT           NULL  COMMENT '°C',
    humidity        FLOAT           NULL  COMMENT '%',
    wind_speed      FLOAT           NULL  COMMENT 'm/s',
    wind_direction  FLOAT           NULL  COMMENT 'degrees',
    pressure        FLOAT           NULL  COMMENT 'hPa',
    aqi             FLOAT           NULL  COMMENT 'Calculated AQI',
    aqi_category    VARCHAR(50)     NULL,
    source          VARCHAR(100)    NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_readings_city        (city),
    KEY idx_readings_recorded_at (recorded_at),
    KEY idx_readings_dataset_id  (dataset_id),
    KEY idx_readings_aqi         (aqi),
    CONSTRAINT fk_readings_dataset FOREIGN KEY (dataset_id)
        REFERENCES datasets (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- TABLE: ml_models
-- Registry of trained ML models and their metrics.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ml_models (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name            VARCHAR(100)    NOT NULL,
    algorithm       ENUM(
                        'linear_regression',
                        'decision_tree',
                        'random_forest',
                        'xgboost',
                        'lightgbm',
                        'lstm'
                    )               NOT NULL,
    version         VARCHAR(20)     NOT NULL DEFAULT '1.0.0',
    file_path       VARCHAR(512)    NOT NULL,
    scaler_path     VARCHAR(512)    NULL,
    feature_names   JSON            NULL,
    hyperparameters JSON            NULL,
    mae             FLOAT           NULL  COMMENT 'Mean Absolute Error',
    rmse            FLOAT           NULL  COMMENT 'Root Mean Squared Error',
    mse             FLOAT           NULL  COMMENT 'Mean Squared Error',
    r2_score        FLOAT           NULL  COMMENT 'R² Score',
    training_time_s FLOAT           NULL,
    train_size      INT             NULL,
    test_size       INT             NULL,
    is_active       BOOLEAN         NOT NULL DEFAULT FALSE,
    trained_by      INT UNSIGNED    NULL,
    trained_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_mlmodels_algorithm  (algorithm),
    KEY idx_mlmodels_is_active  (is_active),
    KEY idx_mlmodels_trained_by (trained_by),
    CONSTRAINT fk_mlmodels_user FOREIGN KEY (trained_by)
        REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- TABLE: predictions
-- Every prediction request and its result.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED    NULL,
    model_id        INT UNSIGNED    NULL,
    city            VARCHAR(100)    NULL,
    input_features  JSON            NOT NULL,
    predicted_aqi   FLOAT           NOT NULL,
    aqi_category    VARCHAR(50)     NULL,
    health_advisory TEXT            NULL,
    confidence      FLOAT           NULL,
    explanation     JSON            NULL   COMMENT 'SHAP/LIME values',
    ip_address      VARCHAR(45)     NULL,
    requested_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_predictions_user_id     (user_id),
    KEY idx_predictions_model_id    (model_id),
    KEY idx_predictions_city        (city),
    KEY idx_predictions_requested_at(requested_at),
    CONSTRAINT fk_predictions_user  FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE SET NULL,
    CONSTRAINT fk_predictions_model FOREIGN KEY (model_id)
        REFERENCES ml_models (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- TABLE: reports
-- Generated PDF/CSV report metadata.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    user_id         INT UNSIGNED    NULL,
    title           VARCHAR(255)    NOT NULL,
    report_type     ENUM(
                        'prediction_history',
                        'analytics',
                        'model_comparison',
                        'eda'
                    )               NOT NULL,
    format          ENUM('pdf','csv','xlsx')  NOT NULL DEFAULT 'pdf',
    file_path       VARCHAR(512)    NULL,
    parameters      JSON            NULL   COMMENT 'Filters applied when generating',
    file_size_kb    INT UNSIGNED    NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_reports_user_id    (user_id),
    KEY idx_reports_created_at (created_at),
    CONSTRAINT fk_reports_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- TABLE: audit_logs
-- Immutable audit trail for security-relevant events.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED    NULL,
    action      VARCHAR(100)    NOT NULL,
    entity      VARCHAR(100)    NULL   COMMENT 'Table / resource affected',
    entity_id   VARCHAR(100)    NULL,
    old_value   JSON            NULL,
    new_value   JSON            NULL,
    ip_address  VARCHAR(45)     NULL,
    user_agent  VARCHAR(512)    NULL,
    status      ENUM('success','failure') NOT NULL DEFAULT 'success',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_audit_user_id    (user_id),
    KEY idx_audit_action     (action),
    KEY idx_audit_created_at (created_at),
    KEY idx_audit_entity     (entity, entity_id),
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id)
        REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
