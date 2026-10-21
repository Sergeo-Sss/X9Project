"""Scan nearby BLE devices and highlight ones that look like the X9-CALL watch."""
import asyncio
import sys

from bleak import BleakScanner

CLASSIC_MAC = "40:45:DA:A9:61:A5"


async def main():
    print("Scanning for 15 seconds...")
    found = await BleakScanner.discover(timeout=15.0, return_adv=True)
    for addr, (dev, adv) in sorted(found.items(), key=lambda kv: -kv[1][1].rssi):
        name = dev.name or adv.local_name or "?"
        mark = ""
        if "X9" in name.upper() or addr.upper()[:8] == CLASSIC_MAC[:8]:
            mark = "  <== candidate"
        print(f"{addr}  rssi={adv.rssi:>4}  name={name}{mark}")
        if mark or "-v" in sys.argv:
            print(f"    service_uuids={adv.service_uuids}")
            print(f"    manufacturer_data={ {k: v.hex() for k, v in adv.manufacturer_data.items()} }")


asyncio.run(main())
