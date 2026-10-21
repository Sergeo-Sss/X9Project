"""Upload a file to the watch over FTP: python ftp_put.py <local> [remote_dir]."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "reader", "tools"))
from watch import connect  # noqa: E402

local = sys.argv[1]
remote_dir = sys.argv[2] if len(sys.argv) > 2 else "/device/Download"
name = os.path.basename(local)

ftp = connect()
ftp.cwd(remote_dir)
with open(local, "rb") as f:
    ftp.storbinary(f"STOR {name}", f)
print(f"uploaded {name} ({os.path.getsize(local)} bytes) to {remote_dir}")
lines = []
ftp.retrlines(f"LIST {name}", lines.append)
for ln in lines:
    print(ln)
ftp.quit()
