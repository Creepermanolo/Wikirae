@echo off

set "SITE_DIR=%~dp0"

echo Generation de pages.json...
node "%SITE_DIR%generate-pages.js"

if errorlevel 1 (
    echo.
    echo Erreur : generate-pages.js n'a pas pu s'executer.
    pause
    exit /b 1
)

echo.
echo Demarrage du serveur local...
echo Ouvrez http://localhost:8000
echo.

python -m http.server 8000 --directory "%SITE_DIR%"

pause