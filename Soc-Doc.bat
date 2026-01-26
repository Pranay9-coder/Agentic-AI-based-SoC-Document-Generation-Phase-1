::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAjk
::fBw5plQjdCyDJGyX8VAjFBpHWRe+GGStCLkT6ezo0/mIoUkSV6w2e4C7
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSzk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCuDJBi0xm0aDThgfzi3D1/6IKAQ5NTv/euJsUsSRu8HRJvJ27qdJu8B5wjlfNs+w3NOnYYBDRJWQiCeQDAEm0Fok0execKEtm8=
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
title Transform AI Suite - Auto Setup Launcher
color 0A

:: Get the directory where this batch file is located
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo.
echo ============================================================
echo    Transform AI Suite - SoC-DoC Auto Launcher
echo ============================================================
echo.

:: ============================================================
:: STEP 1: Check Python Installation
:: ============================================================
echo [1/10] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Found: %PYTHON_VERSION%
echo.

:: ============================================================
:: STEP 2: Check Node.js Installation
:: ============================================================
echo [2/10] Checking Node.js installation...
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo [OK] Found Node: %NODE_VERSION%

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is not available!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version 2^>^&1') do set NPM_VERSION=%%i
echo [OK] Found npm: %NPM_VERSION%
echo.

:: ============================================================
:: STEP 3: Verify Project Structure
:: ============================================================
echo [3/10] Verifying project structure...

if not exist "backend" (
    echo [ERROR] Backend folder not found!
    echo [INFO] Current directory: %CD%
    echo.
    pause
    exit /b 1
)

if not exist "backend\requirements.txt" (
    echo [ERROR] requirements.txt not found in backend folder!
    echo.
    pause
    exit /b 1
)

if not exist "package.json" (
    echo [ERROR] package.json not found in project root!
    echo.
    pause
    exit /b 1
)

echo [OK] Project structure verified
echo.

:: ============================================================
:: STEP 4: Create Python Virtual Environment (if missing)
:: ============================================================
echo [4/10] Checking Python virtual environment...

if exist "backend\venv\Scripts\activate.bat" (
    echo [OK] Virtual environment already exists
) else (
    echo [SETUP] Creating virtual environment...
    echo [INFO] This may take a minute...
    
    cd /d "%PROJECT_DIR%backend"
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        cd /d "%PROJECT_DIR%"
        pause
        exit /b 1
    )
    cd /d "%PROJECT_DIR%"
    
    echo [OK] Virtual environment created successfully
)
echo.

:: ============================================================
:: STEP 5: Install Python Dependencies (if needed)
:: ============================================================
echo [5/10] Checking Python dependencies...

if exist "backend\.dependencies_installed" (
    echo [OK] Python dependencies already installed
    echo [INFO] To reinstall, delete: backend\.dependencies_installed
) else (
    echo [SETUP] Installing Python dependencies...
    echo [INFO] This may take several minutes on first run...
    echo.
    
    cd /d "%PROJECT_DIR%backend"
    
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo [ERROR] Failed to activate virtual environment!
        cd /d "%PROJECT_DIR%"
        pause
        exit /b 1
    )
    
    echo [INFO] Upgrading pip...
    python -m pip install --upgrade pip --quiet
    
    echo [INFO] Installing packages from requirements.txt...
    pip install -r requirements.txt --quiet
    
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install Python dependencies!
        echo [INFO] Try running manually: 
        echo        cd backend
        echo        venv\Scripts\activate
        echo        pip install -r requirements.txt
        cd /d "%PROJECT_DIR%"
        pause
        exit /b 1
    )
    
    echo. > .dependencies_installed
    call deactivate >nul 2>&1
    cd /d "%PROJECT_DIR%"
    
    echo [OK] Python dependencies installed successfully
)
echo.

:: ============================================================
:: STEP 6: Check Environment Configuration
:: ============================================================
echo [6/10] Checking environment configuration...

if exist "backend\.env" (
    echo [OK] Environment file found
) else (
    if exist "backend\.env.example" (
        echo [INFO] No .env file found, but .env.example exists
        echo.
        copy "backend\.env.example" "backend\.env" >nul 2>&1
        if errorlevel 1 (
            echo [WARNING] Could not copy .env.example to .env
        ) else (
            echo [OK] Created .env from template
            echo [WARNING] Please edit backend\.env and add your API keys
        )
    ) else (
        echo [ERROR] No .env or .env.example file found!
        echo.
        echo Please create backend\.env manually with required variables.
        echo.
        pause
        exit /b 1
    )
)
echo.

:: ============================================================
:: STEP 7: Install Frontend Dependencies (if needed)
:: ============================================================
echo [7/10] Checking frontend dependencies...

if exist "node_modules" (
    echo [OK] Frontend dependencies already installed
    echo [INFO] To reinstall, delete: node_modules folder
) else (
    echo [SETUP] Installing frontend dependencies...
    echo [INFO] This may take several minutes on first run...
    echo.
    
    call npm install --loglevel=error
    
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install frontend dependencies!
        echo [INFO] Try running manually: npm install
        pause
        exit /b 1
    )
    
    echo [OK] Frontend dependencies installed successfully
)
echo.

:: ============================================================
:: STEP 8: Clean Up Ports
:: ============================================================
echo [8/10] Cleaning up ports...

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

for %%p in (5173 8080 8081 8082) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr :%%p ^| findstr LISTENING') do (
        taskkill /F /PID %%a >nul 2>&1
    )
)

timeout /t 1 /nobreak >nul
echo [OK] Ports cleaned
echo.

:: ============================================================
:: STEP 9: Start Backend Server
:: ============================================================
echo [9/10] Starting backend server...

start "Transform AI Backend" cmd /k "cd /d "%PROJECT_DIR%backend" && venv\Scripts\activate && python run_server.py"

echo [INFO] Backend starting on http://localhost:5000
echo [INFO] Waiting for backend to initialize...

for /l %%i in (1,1,10) do (
    timeout /t 1 /nobreak >nul
    netstat -an 2>nul | findstr ":5000.*LISTENING" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Backend is ready!
        goto backend_ready
    )
)

:backend_ready
echo.

:: ============================================================
:: STEP 10: Start Frontend Server
:: ============================================================
echo [10/10] Starting frontend server...

start "Transform AI Frontend" cmd /k "cd /d "%PROJECT_DIR%" && npm run dev"

echo [INFO] Frontend starting (Vite will use first available port)
echo [INFO] Waiting for frontend to initialize...

set FRONTEND_PORT=8080
for /l %%i in (1,1,12) do (
    timeout /t 1 /nobreak >nul
    
    for %%p in (8080 8081 8082 5173) do (
        netstat -an 2>nul | findstr ":%%p.*LISTENING" >nul 2>&1
        if not errorlevel 1 (
            set FRONTEND_PORT=%%p
            echo [OK] Frontend is ready on port %%p!
            goto frontend_ready
        )
    )
)

:frontend_ready

set FRONTEND_URL=http://localhost:%FRONTEND_PORT%
echo.

:: ============================================================
:: Open Browser
:: ============================================================
echo [LAUNCH] Opening application in browser...
timeout /t 2 /nobreak >nul
start "" "%FRONTEND_URL%"

echo.
echo ============================================================
echo    APPLICATION LAUNCHED SUCCESSFULLY!
echo ============================================================
echo.
echo    Backend:  http://localhost:5000
echo    Frontend: %FRONTEND_URL%
echo.
echo    [+] Two console windows are now running:
echo        1. Backend Server (Python/Flask)
echo        2. Frontend Server (Node/Vite)
echo.
echo    [!] IMPORTANT: Keep both windows open while using the app
echo.
echo    To stop the application:
echo    - Close both console windows, OR
echo    - Press Ctrl+C in each window
echo.
echo ============================================================
echo.
echo Press any key to close this launcher window...
echo (Backend and frontend will continue running)
echo ============================================================
pause >nul