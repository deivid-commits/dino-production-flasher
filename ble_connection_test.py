import asyncio
import bleak

TARGET_MAC = "D0:CF:13:25:AB:BE"

async def main():
    print(f"Iniciando prueba de conexión para MAC: {TARGET_MAC}")
    
    found_device = None
    max_retries = 3
    for attempt in range(max_retries):
        print(f"--- Intento {attempt + 1}/{max_retries} ---")
        print("🔎 Escaneando dispositivos Bluetooth LE...")
        try:
            devices = await bleak.BleakScanner.discover(timeout=7.0)
            if not devices:
                print("  - No se encontraron dispositivos en este escaneo.")
                continue

            print(f"  - Se encontraron {len(devices)} dispositivos.")
            for device in devices:
                print(f"    - {device.address} | Nombre: {device.name or 'Desconocido'}")
                if device.address.upper() == TARGET_MAC.upper():
                    print(f"🎯 ¡Coincidencia de MAC encontrada! Dispositivo: {device}")
                    found_device = device
                    break
            if found_device:
                break
        except Exception as e:
            print(f"  - Error durante el escaneo: {e}")
        
        if not found_device:
            print("  - MAC no encontrada. Reintentando en 2 segundos...")
            await asyncio.sleep(2)

    if not found_device:
        print(f"\n❌ CRÍTICO: No se pudo encontrar el dispositivo con MAC {TARGET_MAC} después de {max_retries} intentos.")
        return

    print(f"\n✅ Dispositivo encontrado. Intentando conectar a {found_device.address}...")
    try:
        async with bleak.BleakClient(found_device.address) as client:
            is_connected = await client.is_connected()
            if is_connected:
                print("🚀 ¡CONEXIÓN EXITOSA!")
                print("Servicios encontrados:")
                for service in client.services:
                    print(f"  - {service}")
            else:
                print("❌ Fallo al conectar (el cliente no reportó conexión).")
    except Exception as e:
        import traceback
        print(f"❌ CRÍTICO: Ocurrió un error durante la conexión: {e}")
        print("--- TRACEBACK COMPLETO ---")
        traceback.print_exc()
        print("--------------------------")

if __name__ == "__main__":
    asyncio.run(main())
