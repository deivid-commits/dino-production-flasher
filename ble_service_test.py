import asyncio
import bleak

SERVICE_UUID = "a07498ca-ad5b-474e-940d-16f1fbe7e8cd"

async def main():
    print(f"Iniciando prueba de conexión por Service UUID: {SERVICE_UUID}")
    
    found_device = None
    max_retries = 3
    for attempt in range(max_retries):
        print(f"--- Intento {attempt + 1}/{max_retries} ---")
        print(f"🔎 Escaneando dispositivos que anuncian el servicio...")
        try:
            # Scan specifically for devices advertising the service UUID
            devices = await bleak.BleakScanner.discover(service_uuids=[SERVICE_UUID], timeout=10.0)
            
            if devices:
                # Take the first one found
                found_device = devices[0]
                print(f"🎯 ¡Dispositivo encontrado! {found_device}")
                break
            else:
                print("  - No se encontraron dispositivos con ese servicio.")

        except Exception as e:
            print(f"  - Error durante el escaneo: {e}")
        
        if not found_device:
            print("  - Reintentando en 2 segundos...")
            await asyncio.sleep(2)

    if not found_device:
        print(f"\n❌ CRÍTICO: No se pudo encontrar el dispositivo con el Service UUID después de {max_retries} intentos.")
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
