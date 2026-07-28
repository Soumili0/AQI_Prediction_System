-- Seed: Default Admin User
-- Password: Admin@12345  (bcrypt hash — change immediately after first login)
-- Generate a new hash: python -c "from flask_bcrypt import Bcrypt; b=Bcrypt(); print(b.generate_password_hash('Admin@12345').decode())"

USE aqi_prediction_db;

INSERT IGNORE INTO users (
    role_id, email, username, password_hash,
    first_name, last_name, is_active, is_verified
)
SELECT
    r.id,
    'admin@aqisystem.local',
    'sysadmin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uEv2',
    'System', 'Admin', TRUE, TRUE
FROM roles r
WHERE r.name = 'admin'
LIMIT 1;
