@echo off
cd /d "%~dp0"
echo Make sure the test system is running: http://127.0.0.1:5000
py -3 -m pytest
pause
