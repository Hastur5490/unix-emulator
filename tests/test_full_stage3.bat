@echo off
cd /d "%~dp0.."
echo Полный тест Этапа 3
py src/main.py --vfs vfs/deep.csv --script test_all.txt
pause