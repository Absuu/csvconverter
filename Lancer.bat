@echo off
setlocal
set "DIR=%~dp0"
set "EXE=%DIR%ConvertisseurCSV.exe"

if not exist "%EXE%" (
    echo Fichier introuvable : ConvertisseurCSV.exe
    echo Pensez a extraire le .zip avant de lancer ce fichier.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -LiteralPath '%DIR%' -Recurse | Unblock-File"
start "" "%EXE%"
