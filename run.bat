@echo off
echo ===================================================
echo Industrial Troubleshooting Copilot - Startup Script
echo ===================================================

:: Check for .venv directory
if not exist ".venv" (
    echo Error: .venv directory not found. 
    echo Please make sure you have created the virtual environment.
    pause
    exit /b 1
)

:: Check for node_modules in frontend
if not exist "app\frontend\node_modules" (
    echo Warning: app\frontend\node_modules not found.
    echo Running npm install in app\frontend...
    pushd app\frontend
    call npm install
    popd
)

:: Check .env file for OpenAI Key
findstr "OPENAI_API_KEY=" .env >nul
if %errorlevel% == 0 (
    for /f "tokens=2 delims==" %%a in ('findstr "OPENAI_API_KEY=" .env') do (
        if "%%a" == "" (
            echo [IMPORTANT] OPENAI_API_KEY is empty in .env file.
            echo The application might not function correctly without it.
        )
    )
)

echo.
echo Starting Backend (FastAPI on port 8000)...
start "Backend Server" cmd /k ".\.venv\Scripts\python -m uvicorn app.backend.main:app --host 127.0.0.1 --port 8000"

echo.
echo Starting Frontend (Next.js on port 3000)...
echo ===================================================
echo PLEASE OPEN YOUR BROWSER TO: http://localhost:3000
echo ===================================================
echo.
echo Press Ctrl+C in this window to stop the frontend.
cd app\frontend
npm run dev
