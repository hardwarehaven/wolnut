# WOLNUT

**WOLNUT** is a lightweight Python service designed to work alongside [NUT (Network UPS Tools)](https://networkupstools.org/) to automatically send Wake-on-LAN (WOL) packets to client systems after a power outage.

wolnut... get it?

## What It Does

When a UPS (connected to NUT) switches to battery power, WOLNUT:

1. Detects the power event via `upsc`
2. Tracks which clients were online before the outage
3. Waits for power to be restored and the battery to reach a safe threshold
4. Sends WOL packets to bring back any systems that powered down

This helps reboot systems automatically after a controlled shutdown caused by a power loss — especially useful for homelabs, small servers, and media boxes.

---

## Features

- Auto-detect MAC addresses with ARP
- Tracks online status of clients via ping
- Supports NUT with or without authentication
- Persistent state file for post-reboot recovery
- Runs as a standalone Python service or Docker container
- Supports external notifications via [Apprise](https://github.com/caronc/apprise/wiki) URLs

---

## Docker

WOLNUT looks for /config/config.yaml on startup. 

```bash
mkdir ~/wolnut
touch config.yaml
```
Then copy the example.config.yaml as a starting point. 
### Docker Run
```bash
docker run -d \
  --name wolnut \
  --restart unless-stopped \
  -v ~/wolnut:/config \
  --network host \
  hardwarehaven/wolnut:latest
```