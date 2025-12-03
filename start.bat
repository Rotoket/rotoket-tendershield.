@echo off
echo ========================================
echo   Tender Shield Pro - Запуск системы
echo ========================================
echo.

echo [1/3] Запуск Backend...
start "Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] Запуск Frontend...
start "Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 2 /nobreak >nul

echo [3/3] Система запущена!
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Нажмите любую клавишу для выхода...
pause >nul

