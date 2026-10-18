@echo off
cd /d "%~dp0.."
echo Тест с --vfs и --script
py src/main.py --vfs vfs/deep.csv --script tests\test_all.txt
pause