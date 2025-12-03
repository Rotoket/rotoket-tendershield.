# Скрипт проверки статуса сервисов
Write-Host "Проверка статуса сервисов..." -ForegroundColor Cyan

# Проверка Backend
try {
    $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/docs" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($backendResponse.StatusCode -eq 200) {
        Write-Host "✅ Backend: ЗАПУЩЕН (http://localhost:8000)" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Backend: НЕ ЗАПУЩЕН" -ForegroundColor Red
    Write-Host "   Запустите: cd backend && .\venv\Scripts\Activate.ps1 && uvicorn main:app --reload" -ForegroundColor Yellow
}

# Проверка Frontend
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend: ЗАПУЩЕН (http://localhost:5173)" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend: НЕ ЗАПУЩЕН" -ForegroundColor Red
    Write-Host "   Запустите: cd frontend && npm run dev" -ForegroundColor Yellow
}

Write-Host "`nПроверка завершена!" -ForegroundColor Cyan

