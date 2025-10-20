@echo off
echo ========================================
echo    EMONG Worker Manager
echo ========================================
echo.

REM Activate conda environment
echo Activating conda environment...
call conda activate emongonnx

REM Check if Redis is running
echo Checking Redis connection...
python -c "import redis; r = redis.Redis.from_url('redis://localhost:6379/0'); r.ping(); print('✅ Redis is running')" 2>nul
if errorlevel 1 (
    echo ❌ ERROR: Redis is not running!
    echo Please start Redis first.
    echo.
    echo To start Redis:
    echo 1. Install Redis: https://redis.io/download
    echo 2. Start Redis server
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✅ Redis is running. Starting workers...
echo.

REM Test workers first
echo Testing workers...
python test_workers.py
if errorlevel 1 (
    echo ❌ Worker test failed!
    pause
    exit /b 1
)

echo.
echo Starting worker manager...
echo Press Ctrl+C to stop all workers
echo.

REM Start the worker manager
python start_workers_safe.py

echo.
echo Workers stopped.
pause
