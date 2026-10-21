"""Connect to BLE addresses and dump their GATT services/characteristics."""
import asyncio
import sys

from bleak import BleakClient

DEFAULT_ADDRS = ["40:45:DA:A9:61:A5", "7D:DB:13:15:EC:03"]


async def dump(addr):
    print(f"\n=== {addr} ===")
    try:
        async with BleakClient(addr, timeout=20.0) as client:
            print(f"connected: {client.is_connected}")
            for svc in client.services:
                print(f"[service] {svc.uuid}  {svc.description}")
                for ch in svc.characteristics:
                    props = ",".join(ch.properties)
                    line = f"    [char] {ch.uuid}  ({props})  {ch.description}"
                    if "read" in ch.properties:
                        try:
                            val = await client.read_gatt_char(ch)
                            line += f"  = {val.hex()}  {val!r}"
                        except Exception as e:
                            line += f"  read failed: {e}"
                    print(line)
    except Exception as e:
        print(f"failed: {type(e).__name__}: {e}")


async def main():
    for addr in sys.argv[1:] or DEFAULT_ADDRS:
        await dump(addr)


asyncio.run(main())
