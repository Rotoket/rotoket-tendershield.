# Скрипт диагностики подключения Tender Shield Pro

Write-Host "`n=== Диагностика подключения Tender Shield Pro ===`n" -ForegroundColor Cyan

# Проверка порта 8000 (Backend)
Write-Host "1. Проверка Backend (порт 8000)..." -ForegroundColor Yellow
$backendPort = netstat -ano | findstr ":8000"
if ($backendPort) {
    Write-Host "   ✅ Backend запущен на порту 8000" -ForegroundColor Green
} else {
    Write-Host "   ❌ Backend НЕ запущен на порту 8000" -ForegroundColor Red
    Write-Host "   💡 Запустите backend командой:" -ForegroundColor Yellow
    Write-Host "      cd backend" -ForegroundColor Gray
    Write-Host "      .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "      uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
}

# Проверка порта 5173 (Frontend)
Write-Host "`n2. Проверка Frontend (порт 5173)..." -ForegroundColor Yellow
$frontendPort = netstat -ano | findstr ":5173"
if ($frontendPort) {
    Write-Host "   ✅ Frontend запущен на порту 5173" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Frontend не запущен (это нормально, если вы только запускаете)" -ForegroundColor Yellow
}

# Проверка .env файла во frontend
Write-Host "`n3. Проверка конфигурации Frontend..." -ForegroundColor Yellow
$envFile = "frontend\.env"
if (Test-Path $envFile) {
    Write-Host "   ✅ Файл .env найден" -ForegroundColor Green
    $envContent = Get-Content $envFile
    $apiUrl = $envContent | Select-String "VITE_API_URL"
    if ($apiUrl) {
        Write-Host "   ✅ VITE_API_URL настроен: $apiUrl" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  VITE_API_URL не найден в .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ Файл .env не найден" -ForegroundColor Red
    Write-Host "   💡 Создайте файл frontend\.env со следующим содержимым:" -ForegroundColor Yellow
    Write-Host "      VITE_API_URL=http://localhost:8000/api" -ForegroundColor Gray
}

# Проверка доступности API
Write-Host "`n4. Проверка доступности API..." -ForegroundColor Yellow
if ($backendPort) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -Method GET -TimeoutSec 3 -ErrorAction Stop
        $healthData = $response.Content | ConvertFrom-Json
        Write-Host "   ✅ API доступен и работает" -ForegroundColor Green
        Write-Host "   📋 CORS origins: $($healthData.cors_origins -join ', ')" -ForegroundColor Gray
    } catch {
        Write-Host "   ⚠️  Backend запущен, но API не отвечает: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "   💡 Проверьте логи backend" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⏭️  Пропущено (backend не запущен)" -ForegroundColor Gray
}

# Итоговые рекомендации
Write-Host "`n=== Рекомендации ===" -ForegroundColor Cyan

if (-not $backendPort) {
    Write-Host "`n🔴 КРИТИЧНО: Backend не запущен!" -ForegroundColor Red
    Write-Host "   Запустите backend в отдельном терминале:" -ForegroundColor Yellow
    Write-Host "   cd backend" -ForegroundColor Gray
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "   uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
}

if (-not (Test-Path $envFile)) {
    Write-Host "`n⚠️  Создайте файл frontend\.env" -ForegroundColor Yellow
    Write-Host "   Содержимое: VITE_API_URL=http://localhost:8000/api" -ForegroundColor Gray
}

Write-Host "`n✅ После запуска backend, откройте: http://localhost:5173" -ForegroundColor Green
Write-Host ""

