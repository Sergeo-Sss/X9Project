---
name: x9-watch-access
description: >-
  Reach the X9-CALL watch from this PC — find it on the network, browse and
  transfer files over FTP, and understand why ADB/Bluetooth are limited. Use
  when uploading or downloading files on the watch, when FTP stops responding,
  when locating the watch's IP, or when deciding how to get data on/off the
  watch. The watch runs Android 8.1 with Wi-Fi; it is reachable by IP but has no
  open ADB port (no cable with data lines available).
---

# X9-CALL watch access

The watch is a full Android 8.1 device on Wi-Fi, but constrained:

- **BLE**: it does not advertise for a second central while bound to its phone
  app, so the PC usually cannot connect over BLE.
- **Bluetooth classic**: paired for calls/audio only (MAC `40:45:DA:A9:61:A5`).
- **ADB over network**: unavailable. Android 8 has no wireless debugging (added
  in Android 11), and enabling network ADB needs a cable — the charger has only
  2 of the 4 contacts wired, so no USB data. USB debugging is on (engineer menu
  `*#*#83781#*#*`) but useless without a data cable.
- **Wi-Fi / FTP**: the working channel. The watch gets an IP on the LAN
  (seen as `192.168.1.6`, MAC prefix `40:45:DA`). Files move via an FTP server
  the user starts in **CX File Explorer -> Network -> Access from computer**.

## Transfer files

Connection details are in `watch.local.json` at the project root (gitignored):
`host`, `port`, `user`, `password`. **CX regenerates the port and password every
time the FTP server starts**, so when a transfer fails with connection refused,
the server is simply off or has new credentials — ask the user to restart it and
update `watch.local.json`.

```bash
python ftp_ls.py /device            # browse (watch storage is mounted at /device)
python ftp_put.py file.apk /device/Download   # upload
```

`reader/tools/watch.py` holds the shared `connect()` helper that reads the config.

## Find the watch on the network

```bash
python lan_scan.py 192.168.1         # ping-sweep + ARP, lists devices with MAC
python port_scan.py 192.168.1.6      # all TCP ports (expect none open)
```

Note: an active VPN (e.g. AmneziaVPN) can swallow LAN traffic; the user must
exclude the local subnet (split tunneling) for scans to work.

## BLE reconnaissance (reference)

`ble_scan.py` / `ble_dump.py` (need `pip install bleak`) scan and dump GATT —
used while trying BLE first. Kept for reference; FTP is the practical path.

See also: [[x9-reader]] for what gets deployed to the watch.
