$body = '{"email":"admin@aqi.local","password":"Admin@1234"}'
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5000/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $body
    Write-Host "LOGIN: OK" -ForegroundColor Green
    Write-Host "User    : $($response.user.username)"
    Write-Host "Role    : $($response.user.role)"
    Write-Host "Token   : $($response.access_token.Substring(0,30))..."
} catch {
    Write-Host "LOGIN FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ErrorDetails.Message
}
