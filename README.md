# DinoCore Production Flasher

Este software está diseñado para flashear y realizar pruebas de control de calidad (QC) en dispositivos DinoCore en un entorno de producción.

## Características

- Flasheo de firmware en modo "Producción" y "Testing".
- Grabación de eFuse para versionado de hardware.
- Pruebas de QC de Bluetooth LE para el balance de micrófonos.
- Selección de dispositivo Bluetooth manual o automática.
- Registro de logs en archivo local (`session.log`).
- Integración con Firebase para almacenar resultados de flasheo, pruebas de QC y logs de sesión.

## Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/deivid-commits/dino-production-flasher.git
    cd dino-production-flasher
    ```

2.  **Instalar dependencias de Python:**
    Ejecuta el script de instalación para tu sistema operativo:
    -   **Windows:** `install.bat`
    -   **Linux/macOS:** `install.sh`

    Esto creará un entorno virtual e instalará los paquetes listados en `requirements.txt`.

## Configuración de Firebase (¡Importante!)

Para que el programa pueda guardar los logs y resultados en Firebase, necesitas configurar tus credenciales de servicio.

1.  **Obtén tu archivo de credenciales:**
    -   Ve a tu proyecto en la [Consola de Firebase](https://console.firebase.google.com/).
    -   Ve a **Configuración del proyecto** > **Cuentas de servicio**.
    -   Haz clic en **"Generar nueva clave privada"**. Se descargará un archivo JSON.

2.  **Coloca y renombra el archivo:**
    -   Renombra el archivo JSON descargado a `firebase-credentials.json`.
    -   Mueve este archivo a la carpeta `production_flasherv1.2/` dentro del proyecto.

    El programa buscará automáticamente este archivo al iniciarse. **Este archivo no se sube a GitHub y debe permanecer privado.**

    Puedes usar el archivo `firebase-credentials-template.json` como referencia para el formato.

## Uso

Para iniciar la aplicación, ejecuta el siguiente comando desde la raíz del proyecto:

```bash
python production_flasherv1.2/gui_flasher.py
```

O, en Windows, puedes usar el archivo de inicio rápido:

```bash
.\start_gui.bat
```

## Creación de Releases (Automatizado)

Para hacer un commit de los cambios y crear una nueva versión en GitHub, usa el script `release.bat` (en Windows).

```bash
.\release.bat "Tu mensaje de commit aquí"
```

Este script se encargará de:
- Incrementar el número de versión.
- Hacer commit y push de tus cambios.
- Crear un nuevo tag y una release en GitHub.
