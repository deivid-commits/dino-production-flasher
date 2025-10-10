import asyncio
from bleak import BleakScanner

async def main():
    print("--- Iniciando Escaneo de Diagnóstico Bluetooth ---")
    print("Buscando todos los dispositivos y sus datos de advertising completos...")

    try:
        devices = await BleakScanner.discover(return_adv=True, timeout=10.0)
    except Exception as e:
        print(f"Error durante el escaneo: {e}")
        return

    if not devices:
        print("No se encontraron dispositivos.")
        return

    print(f"Se encontraron {len(devices)} dispositivos.")
    print("="*40)

    for device, advertisement_data in devices.values():
        print(f"Dispositivo: {device.address} | Nombre: {device.name or 'N/A'}")
        print(f"  RSSI: {advertisement_data.rssi} dBm")
        if advertisement_data.manufacturer_data:
            for company_id, data in advertisement_data.manufacturer_data.items():
                print(f"  Datos del Fabricante [{company_id}]: {data.hex()}")
        if advertisement_data.service_uuids:
            print(f"  Service UUIDs: {', '.join(advertisement_data.service_uuids)}")
        if advertisement_data.service_data:
            for uuid, data in advertisement_data.service_data.items():
                print(f"  Datos de Servicio [{uuid}]: {data.hex()}")
        print("-" * 20)

    print("--- Escaneo de Diagnóstico Completo ---")

if __name__ == "__main__":
    asyncio.run(main())
