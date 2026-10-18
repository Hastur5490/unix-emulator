@echo off
cd /d "%~dp0.."
echo Тест Этапа 4 (основные команды)
py src/main.py --vfs vfs/deep.csv --script tests/test_stage4.txt
pause