"""Scan all TCP ports of a host: python port_scan.py <ip> [first] [last]."""
import asyncio
import sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.6"
FIRST = int(sys.argv[2]) if len(sys.argv) > 2 else 1
LAST = int(sys.argv[3]) if len(sys.argv) > 3 else 65535


async def probe(port, sem, found):
    async with sem:
        try:
            _, w = await asyncio.wait_for(asyncio.open_connection(HOST, port), 1.0)
            found.append(port)
            w.close()
        except (OSError, asyncio.TimeoutError):
            pass


async def main():
    sem, found = asyncio.Semaphore(500), []
    await asyncio.gather(*(probe(p, sem, found) for p in range(FIRST, LAST + 1)))
    print("open:", sorted(found) or "none")


asyncio.run(main())
