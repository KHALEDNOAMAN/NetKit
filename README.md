<div align="center">
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,100:00d4ff&height=200&section=header&text=NetKit&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=Network%20Diagnostic%20Toolkit&descSize=20&descAlignY=55" width="100%" />

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**One tool. Three network diagnostic powers.**

</div>

---

## What Is NetKit?

NetKit is a lightweight, easy-to-use network diagnostic toolkit that combines WiFi analysis, device discovery, and service health monitoring into a single CLI tool. Instead of juggling multiple tools, run one command and get instant answers.

## Modules

### 1. WiFi Doctor
Diagnose WiFi issues instantly. Find congested channels, measure signal quality, check DNS speed.

```bash
$ netkit wifi

📡 WiFi Health Report
──────────────────────
Signal Strength:  ████████░░  78% (Good)
Channel:          6 (CONGESTED - 12 networks!)
Recommended:      Channel 11 (only 2 networks)
DNS Response:     120ms (SLOW → switch to 1.1.1.1)
```

### 2. Network Mapper
Discover all devices on your network with auto-identification.

```bash
$ netkit scan

🗺️ Network Map
──────────────
🌐 Router (192.168.1.1) - TP-Link
├── 💻 Desktop (192.168.1.101) - Windows
├── 📱 iPhone (192.168.1.102) - Apple
├── 🖨️ Printer (192.168.1.104) - HP
└── ⚠️ Unknown (192.168.1.199) - ??
```

### 3. PortPulse - Service Monitor
Monitor all your services from one config file.

```bash
$ netkit monitor

PortPulse Dashboard
────────────────────
● API Server      UP   12ms   ✅ 99.9%
● PostgreSQL      UP    3ms   ✅ 100%
● Redis           UP    1ms   ✅ 100%
● Nginx           DOWN  ---   🔴 2min ago
```

## Installation

```bash
pip install netkit-cli

# Or from source
git clone https://github.com/KHALEDNOAMAN/NetKit.git
cd NetKit
pip install -e .
```

## Quick Start

```bash
netkit wifi              # WiFi diagnosis
netkit scan              # Discover network devices
netkit monitor           # Service health (needs config)
netkit report            # Full diagnostic report
```

## Configuration

Create `portpulse.yml` for service monitoring:

```yaml
services:
  - name: Web Server
    url: http://localhost:80
    type: http
  - name: Database
    host: localhost
    port: 5432
    type: tcp
  - name: Redis
    host: localhost
    port: 6379
    type: tcp
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| CLI | Click + Rich |
| WiFi Analysis | Scapy + netifaces |
| Network Scan | ARP + Socket |
| Dashboard | Flask + WebSocket |
| Container | Docker |

## Docker

```bash
docker-compose up
# Dashboard at http://localhost:5000
```

## Architecture

```
NetKit CLI
├── wifi-doctor     → Channel analysis, signal quality, DNS check
├── network-mapper  → ARP discovery, device identification, topology
├── port-pulse      → HTTP/TCP checks, SSL expiry, uptime tracking
└── web dashboard   → Flask + real-time WebSocket updates
```





## License

MIT License - see [LICENSE](LICENSE)
