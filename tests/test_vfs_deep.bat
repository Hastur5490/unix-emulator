@echo off
cd /d "%~dp0.."
echo Тест глубокой VFS (3+ уровня)
py src/main.py --vfs vfs/deep.csv
pause