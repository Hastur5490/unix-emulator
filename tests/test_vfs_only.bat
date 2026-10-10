@echo off
cd /d "%~dp0.."
echo Тест только с --vfs
py src/main.py --vfs C:\temp\vfs
pause