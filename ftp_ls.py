"""List a directory on the watch over FTP: python ftp_ls.py [path]."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "reader", "tools"))
from watch import connect  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else "/"

ftp = connect()
print("connected:", ftp.getwelcome())
ftp.cwd(path)
print("dir:", ftp.pwd())
lines = []
ftp.retrlines("LIST", lines.append)
for ln in lines:
    print(ln)
ftp.quit()
