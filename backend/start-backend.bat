@echo off
cd /d "C:\Users\Dom\Desktop\tender-shield-pro\backend"
call venv\Scripts\activate.bat
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause

