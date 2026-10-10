@echo off
cd /d "%~dp0.."
echo Тест минимальной VFS
py src/main.py --vfs vfs/minimal.csv
pause