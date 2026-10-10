@echo off
cd /d "%~dp0.."
echo Тест Этапа 5
py src/main.py --vfs vfs/deep.csv --script test_stage5.txt
pause