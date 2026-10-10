@echo off
cd /d "%~dp0.."
echo Тест с --vfs и --script
py src/main.py --vfs C:\temp\vfs --script test_script.txt
pause