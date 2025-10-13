@echo off
setlocal enabledelayedexpansion

REM --- Script AUTOMATICO para crear releases en GitHub ---

REM 1. Leer la versión actual del archivo version.txt
set /p CURRENT_VERSION=<version.txt
echo Version Actual: %CURRENT_VERSION%

REM 2. Separar la versión en sus componentes (major.minor.patch)
for /f "tokens=1,2,3 delims=." %%a in ("%CURRENT_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)

REM 3. Incrementar el número de parche
set /a NEW_PATCH=%PATCH% + 1
set NEW_VERSION=%MAJOR%.%MINOR%.%NEW_PATCH%
echo Nueva Version: %NEW_VERSION%

REM 4. Generar mensaje automático
set "COMMIT_MESSAGE=Release v%NEW_VERSION%"
echo Mensaje: %COMMIT_MESSAGE%

REM 5. Actualizar el archivo de versión PRIMERO
echo %NEW_VERSION% > version.txt

REM 6. Ejecutar los comandos de Git
echo.
echo --- Ejecutando comandos de Git ---
git add .
git commit -m "%COMMIT_MESSAGE%"
git push

REM 7. Crear tag y subirlo
echo.
echo --- Creando y subiendo tag ---
git tag v%NEW_VERSION%
git push origin v%NEW_VERSION%

REM 8. Crear archivo ZIP del proyecto
echo.
echo --- Creando archivo ZIP del proyecto ---
set ZIP_FILENAME=dino-production-flasher-v%NEW_VERSION%.zip
tar -acf %ZIP_FILENAME% --exclude=".git" --exclude="backup" --exclude="*.zip" --exclude="*.log" --exclude="production_firmware" --exclude="testing_firmware" production_flasherv1.2

REM 9. Crear release en GitHub y subir el ZIP
echo.
echo --- Creando release en GitHub ---
gh release create v%NEW_VERSION% --title "Release v%NEW_VERSION%" --notes "%COMMIT_MESSAGE%" %ZIP_FILENAME%

REM 10. Limpiar el archivo ZIP local
del %ZIP_FILENAME%

echo.
echo --- Proceso completado ---
echo Version %NEW_VERSION% ha sido creada y subida a GitHub.
pause
