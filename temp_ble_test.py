import asyncio
import bleak

async def main():
    print("Buscando dispositivo 'Toy-ABBC'...")
    device = await bleak.BleakScanner.find_device_by_name('Toy-ABBC', timeout=10.0)
    if device:
        print(f"--- ¡Dispositivo encontrado! ---")
        print(f"Nombre: {device.name}")
        print(f"Dirección: {device.address}")
        print(f"Detalles: {device.details}")
    else:
        print("--- Dispositivo no encontrado. ---")

if __name__ == "__main__":
    asyncio.run(main())
