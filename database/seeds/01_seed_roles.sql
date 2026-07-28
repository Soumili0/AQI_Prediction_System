-- Seed: Application Roles
-- Run after schema.sql to ensure roles exist

USE aqi_prediction_db;

INSERT IGNORE INTO roles (name, description) VALUES
    ('admin',        'Full system access; manages users, models, and audit logs'),
    ('researcher',   'Access to datasets, notebooks, model training, and XAI reports'),
    ('policy_maker', 'Read-only analytics, reports, and prediction history'),
    ('citizen',      'Public-facing prediction and health advisory features');
