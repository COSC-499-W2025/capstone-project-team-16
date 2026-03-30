@echo off

:: Check for Python using the 'py' launcher
py -3 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 not found.
    echo Please install Python 3 from python.org and try again.
    echo Make sure to check "Add python.exe to PATH" during installation.
    pause
    exit /b
)

:: Check for Node.js/npm
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js/npm not found.
    echo Please install Node.js from nodejs.org and try again.
    pause
    exit /b
)

echo ==========================================
echo Starting Skill Scope (Windows)
echo ==========================================

echo [1/3] Installing Python dependencies...
py -3 -m pip install -r requirements.txt

echo [2/3] Starting Backend API...
set PORT=8000
set SKILLSCOPE_API_URL=http://127.0.0.1:8000
start cmd /k "py -3 src/api.py"

echo [3/3] Starting Frontend UI...
cd src\ui
set VITE_API_BASE_URL=http://127.0.0.1:8000
set REACT_APP_API_URL=http://127.0.0.1:8000
call npm install
npm run dev