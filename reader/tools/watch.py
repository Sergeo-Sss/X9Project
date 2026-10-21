"""Shared helpers for talking to the watch over FTP.

Connection details live in watch.local.json at the project root (gitignored), so no
credentials are committed. Copy watch.local.example.json to watch.local.json and set
the host/port/user/password that CX File Explorer shows under "Доступ с компьютера".
"""
import json
import os
from ftplib import FTP

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG = os.path.join(ROOT, "watch.local.json")


def load_config():
    if not os.path.exists(CONFIG):
        raise SystemExit(
            "watch.local.json not found.\n"
            "Copy watch.local.example.json to watch.local.json and set the FTP\n"
            "host/port/user/password from CX File Explorer on the watch."
        )
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)


def connect(timeout=30):
    cfg = load_config()
    ftp = FTP()
    ftp.connect(cfg["host"], int(cfg["port"]), timeout=timeout)
    ftp.login(cfg["user"], cfg["password"])
    return ftp
