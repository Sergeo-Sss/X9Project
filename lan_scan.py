"""Ping-sweep a /24 subnet, then list live hosts with MAC (from ARP) and hostname."""
import concurrent.futures
import re
import socket
import subprocess
import sys

PREFIX = sys.argv[1] if len(sys.argv) > 1 else "192.168.1"


def ping(ip):
    r = subprocess.run(["ping", "-n", "1", "-w", "500", ip], capture_output=True)
    return ip if r.returncode == 0 else None


def hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except OSError:
        return ""


with concurrent.futures.ThreadPoolExecutor(64) as ex:
    alive = {ip for ip in ex.map(ping, [f"{PREFIX}.{i}" for i in range(1, 255)]) if ip}

arp = subprocess.run(["arp", "-a"], capture_output=True, text=True, encoding="cp866").stdout
macs = dict(re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-f-]{17})", arp))

for ip in sorted(alive | {i for i in macs if i.startswith(PREFIX + ".")},
                 key=lambda s: int(s.rsplit(".", 1)[1])):
    if ip.endswith(".255"):
        continue
    print(f"{ip:<15} {macs.get(ip, '-'):<18} {'ping' if ip in alive else 'arp '}  {hostname(ip)}")
