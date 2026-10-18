@echo off
cd /d "%~dp0.."
echo Полный тест Этапа 3
py src/main.py --vfs vfs/deep.csv --script tests/test_all.txt
pause