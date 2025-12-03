@echo off
echo Запуск Backend и Frontend...
start "Tender Shield - Backend" cmd /k "cd /d C:\Users\Dom\Desktop\tender-shield-pro\backend && venv\Scripts\activate.bat && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul
start "Tender Shield - Frontend" cmd /k "cd /d C:\Users\Dom\Desktop\tender-shield-pro\frontend && npm run dev"
echo.
echo ✅ Сервисы запущены!
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Нажмите любую клавишу для закрытия этого окна...
pause >nul

