$base = "http://localhost:5000/api/v1"

# 1. Login
$body = '{"email":"admin@aqi.local","password":"Admin@1234"}'
$login = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" -Body $body
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
Write-Host "1. LOGIN         : OK — user=$($login.user.username) role=$($login.user.role)" -ForegroundColor Green

# 2. /me
$me = Invoke-RestMethod -Uri "$base/auth/me" -Headers $headers
Write-Host "2. GET /me       : OK — $($me.user.email)" -ForegroundColor Green

# 3. Analytics overview
$ov = Invoke-RestMethod -Uri "$base/analytics/overview?days=30" -Headers $headers
Write-Host "3. Analytics OV  : OK — mean_aqi=$($ov.mean_aqi) city=$($ov.city)" -ForegroundColor Green

# 4. Analytics cities
$cities = Invoke-RestMethod -Uri "$base/analytics/cities" -Headers $headers
Write-Host "4. Cities        : OK — $($cities.total_cities) cities: $(($cities.cities | ForEach-Object { $_.city }) -join ', ')" -ForegroundColor Green

# 5. Prediction
$pred_body = '{"pm25":85,"pm10":120,"no2":45,"so2":18,"co":1.2,"o3":60,"city":"Delhi"}'
$pred = Invoke-RestMethod -Uri "$base/predictions/" -Method POST -ContentType "application/json" -Body $pred_body -Headers $headers
Write-Host "5. PREDICTION    : OK — AQI=$($pred.predicted_aqi) ($($pred.aqi_category))" -ForegroundColor Green

Write-Host "`nAll checks passed!" -ForegroundColor Cyan
