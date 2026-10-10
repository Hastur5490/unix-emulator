@echo off
cd /d "%~dp0.."
echo Тест простой VFS
py src/main.py --vfs vfs/simple.csv
pause