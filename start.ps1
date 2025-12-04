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

# Проверка и запуск Ollama
Write-Host "[0/4] Проверка и запуск Ollama..." -ForegroundColor Green
$ollamaProcess = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($ollamaProcess) {
    Write-Host "Ollama уже запущен." -ForegroundColor Yellow
} else {
    Write-Host "Запуск Ollama..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Minimized
        Start-Sleep -Seconds 5
        Write-Host "Ollama запущен." -ForegroundColor Green
    } catch {
        Write-Host "[ПРЕДУПРЕЖДЕНИЕ] Не удалось запустить Ollama автоматически." -ForegroundColor Yellow
        Write-Host "Убедитесь, что Ollama установлен и доступен в PATH." -ForegroundColor Yellow
        Write-Host "Попробуйте запустить вручную: ollama serve" -ForegroundColor Yellow
    }
}
Write-Host ""

# Запуск Backend
Write-Host "[1/4] Запуск Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 3

# Запуск Frontend
Write-Host "[2/4] Запуск Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "[3/4] Система запущена!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

