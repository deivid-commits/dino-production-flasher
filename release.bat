@echo off
setlocal enabledelayedexpansion

REM --- Script para automatizar la creación de releases en GitHub ---

REM 1. Leer la versión actual del archivo version.txt
set /p CURRENT_VERSION=<version.txt
echo Versión Actual: %CURRENT_VERSION%

REM 2. Separar la versión en sus componentes (major.minor.patch)
for /f "tokens=1,2,3 delims=." %%a in ("%CURRENT_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)

REM 3. Incrementar el número de parche
set /a NEW_PATCH=%PATCH% + 1
set NEW_VERSION=%MAJOR%.%MINOR%.%NEW_PATCH%
echo Nueva Versión: %NEW_VERSION%

REM 4. Tomar el mensaje del commit del primer argumento
set "COMMIT_MESSAGE=%~1"
if not defined COMMIT_MESSAGE (
    echo ERROR: No se proporcionó un mensaje para el commit.
    echo Uso: release.bat "Tu mensaje aqui"
    pause
    exit /b
)
echo Mensaje del Commit: %COMMIT_MESSAGE%

REM 5. Ejecutar los comandos de Git
echo.
echo --- Ejecutando comandos de Git ---
git add .
git commit -m "%COMMIT_MESSAGE%"
git push

REM 6. Crear archivo ZIP y release en GitHub
echo.
echo --- Creando archivo ZIP del proyecto ---
set ZIP_FILENAME=dino-production-flasher-v%NEW_VERSION%.zip
tar -acf %ZIP_FILENAME% --exclude=".git" --exclude="backup" --exclude="*.zip" --exclude="*.log" --exclude="production_firmware" --exclude="testing_firmware" .
echo.
echo --- Creando release en GitHub y subiendo el ZIP ---
git tag v%NEW_VERSION%
git push origin v%NEW_VERSION%
gh release create v%NEW_VERSION% --title "Release v%NEW_VERSION%" --notes "%COMMIT_MESSAGE%" %ZIP_FILENAME%

REM 7. Limpiar el archivo ZIP local
del %ZIP_FILENAME%

REM 8. Actualizar el archivo de versión
echo %NEW_VERSION% > version.txt
echo.
echo --- Proceso completado ---
echo Versión %NEW_VERSION% ha sido creada y subida a GitHub.
