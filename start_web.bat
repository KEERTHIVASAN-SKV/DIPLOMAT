@echo off
echo Starting DIPLOMAT Web Application...
echo.

REM Start FastAPI backend in a new window
echo [1/2] Starting FastAPI backend on http://localhost:8000
start "DIPLOMAT API" cmd /k "cd /d %~dp0 && venv\Scripts\uvicorn.exe web.api.server:app --reload --port 8000"

REM Wait a moment for the API to start
timeout /t 2 /nobreak > nul

REM Start Next.js frontend
echo [2/2] Starting Next.js frontend on http://localhost:3000
start "DIPLOMAT UI" cmd /k "cd /d %~dp0\web && npm run dev"

echo.
echo Both servers starting...
echo   API:      http://localhost:8000
echo   Frontend: http://localhost:3000
echo.
echo Open http://localhost:3000 in your browser.
pause
