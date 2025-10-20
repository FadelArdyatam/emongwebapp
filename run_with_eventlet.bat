@echo off
echo Starting EMONG Web Application with Eventlet...
echo.

REM Set environment variables
set USE_ONNX_INFERENCE=true
set FLASK_ENV=development
set FLASK_DEBUG=1

echo Environment variables set:
echo - USE_ONNX_INFERENCE=%USE_ONNX_INFERENCE%
echo - FLASK_ENV=%FLASK_ENV%
echo - FLASK_DEBUG=%FLASK_DEBUG%
echo.

echo Starting application...
python start_app_safe.py

pause
