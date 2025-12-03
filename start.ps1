# Tender Shield Pro - Запуск системы (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Tender Shield Pro - Запуск системы" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка виртуального окружения
if (-not (Test-Path "backend\venv\Scripts\Activate.ps1")) {
    Write-Host "[ОШИБКА] Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "Выполните: cd backend && python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Запуск Backend
Write-Host "[1/3] Запуск Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 3

# Запуск Frontend
Write-Host "[2/3] Запуск Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "[3/3] Система запущена!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

