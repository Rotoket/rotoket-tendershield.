# Скрипт запуска Tender Shield Pro

Write-Host "Запуск Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\Dom\Desktop\tender-shield-pro\backend'; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 2

Write-Host "Запуск Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\Dom\Desktop\tender-shield-pro\frontend'; npm run dev"

Write-Host ""
Write-Host "Сервисы запускаются..." -ForegroundColor Yellow
Write-Host "Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Откройте браузер и перейдите на: http://localhost:5173" -ForegroundColor Cyan

