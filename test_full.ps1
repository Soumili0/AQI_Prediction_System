$base = "http://localhost:5000/api/v1"
$ok = $true

# 1. Login
try {
    $body = "{`"email`":`"admin@aqi.local`",`"password`":`"Admin@1234`"}"
    $login = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType "application/json" -Body $body
    $token = $login.access_token
    $headers = @{ Authorization = "Bearer $token" }
    Write-Host "[OK] LOGIN  user=$($login.user.username)  role=$($login.user.role)"
} catch {
    Write-Host "[FAIL] LOGIN: $_"
    $ok = $false
    exit 1
}

# 2. /me
try {
    $me = Invoke-RestMethod -Uri "$base/auth/me" -Headers $headers
    Write-Host "[OK] /me  email=$($me.user.email)"
} catch {
    Write-Host "[FAIL] /me: $_"
    $ok = $false
}

# 3. Analytics overview
try {
    $ov = Invoke-RestMethod -Uri "$base/analytics/overview?days=30" -Headers $headers
    Write-Host "[OK] analytics/overview  mean_aqi=$($ov.mean_aqi)  city=$($ov.city)"
} catch {
    Write-Host "[FAIL] analytics/overview: $_"
    $ok = $false
}

# 4. Cities
try {
    $cities = Invoke-RestMethod -Uri "$base/analytics/cities" -Headers $headers
    $cityNames = ($cities.cities | ForEach-Object { $_.city }) -join ", "
    Write-Host "[OK] analytics/cities  count=$($cities.total_cities)  cities=$cityNames"
} catch {
    Write-Host "[FAIL] analytics/cities: $_"
    $ok = $false
}

# 5. Trend
try {
    $trend = Invoke-RestMethod -Uri "$base/analytics/trend?granularity=daily&days=30" -Headers $headers
    Write-Host "[OK] analytics/trend  points=$($trend.trend.Count)"
} catch {
    Write-Host "[FAIL] analytics/trend: $_"
    $ok = $false
}

# 6. Pollutants
try {
    $poll = Invoke-RestMethod -Uri "$base/analytics/pollutants?days=30" -Headers $headers
    Write-Host "[OK] analytics/pollutants  pm25=$($poll.pollutants.pm25)"
} catch {
    Write-Host "[FAIL] analytics/pollutants: $_"
    $ok = $false
}

# 7. Prediction
try {
    $pbody = "{`"pm25`":85,`"pm10`":120,`"no2`":45,`"so2`":18,`"co`":1.2,`"o3`":60,`"city`":`"Delhi`"}"
    $pred = Invoke-RestMethod -Uri "$base/predictions/" -Method POST -ContentType "application/json" -Body $pbody -Headers $headers
    Write-Host "[OK] prediction  AQI=$($pred.predicted_aqi)  category=$($pred.aqi_category)"
} catch {
    Write-Host "[FAIL] prediction: $($_.ErrorDetails.Message)"
    $ok = $false
}

if ($ok) {
    Write-Host ""
    Write-Host "All checks passed!"
} else {
    Write-Host ""
    Write-Host "Some checks failed. See above."
}
