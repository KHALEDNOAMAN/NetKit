"""Network Mapper - Discover all devices on your network."""
import socket
import subprocess
import platform
from dataclasses import dataclass
from typing import Optional
from rich.console import Console
from rich.tree import Tree
from rich.table import Table
from rich import box

from netkit.utils import get_local_ip, get_gateway, get_subnet, is_port_open

console = Console()

DEVICE_ICONS = {
    "router": "🌐", "desktop": "💻", "laptop": "💻", "phone": "📱",
    "printer": "🖨️", "camera": "📷", "tv": "📺", "iot": "🔌",
    "server": "🖥️", "unknown": "❓",
}

COMMON_PORTS = {
    22: "SSH", 80: "HTTP", 443: "HTTPS", 445: "SMB",
    548: "AFP", 3389: "RDP", 5000: "UPnP", 8080: "HTTP-Alt",
    631: "Printer", 9100: "Printer-Raw", 554: "RTSP",
}


@dataclass
class NetworkDevice:
    ip: str
    mac: str = ""
    hostname: str = ""
    vendor: str = ""
    device_type: str = "unknown"
    open_ports: list = None
    is_gateway: bool = False

    def __post_init__(self):
        if self.open_ports is None:
            self.open_ports = []


class NetworkMapper:
    def __init__(self, subnet: Optional[str] = None, timeout: int = 3):
        self.subnet = subnet or get_subnet()
        self.timeout = timeout
        self.gateway = get_gateway()
        self.local_ip = get_local_ip()

    def discover(self) -> list:
        """Discover all devices on the network."""
        devices = []
        arp_table = self._get_arp_table()

        for ip, mac in arp_table.items():
            device = NetworkDevice(ip=ip, mac=mac)
            device.hostname = self._resolve_hostname(ip)
            device.vendor = self._guess_vendor(mac)
            device.is_gateway = (ip == self.gateway)
            device.device_type = self._guess_device_type(device)
            device.open_ports = self._quick_port_scan(ip)
            devices.append(device)

        devices.sort(key=lambda d: (not d.is_gateway, d.ip))
        return devices

    def _get_arp_table(self) -> dict:
        """Get ARP table from system."""
        table = {}
        system = platform.system().lower()
        try:
            if system == "windows":
                output = subprocess.run(
                    ["arp", "-a"], capture_output=True, text=True, timeout=10
                )
                for line in output.stdout.split("\n"):
                    parts = line.split()
                    if len(parts) >= 3 and parts[0].count(".") == 3:
                        ip, mac = parts[0], parts[1]
                        if mac != "ff-ff-ff-ff-ff-ff" and not ip.endswith(".255"):
                            table[ip] = mac.replace("-", ":")
            else:
                output = subprocess.run(
                    ["arp", "-an"], capture_output=True, text=True, timeout=10
                )
                for line in output.stdout.split("\n"):
                    if "ether" in line or "at" in line:
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if p.count(".") == 3:
                                ip = p.strip("()")
                                for m in parts:
                                    if m.count(":") == 5:
                                        table[ip] = m
                                        break
        except Exception:
            pass

        if self.gateway not in table:
            table[self.gateway] = "00:00:00:00:00:00"
        if self.local_ip not in table:
            table[self.local_ip] = "self"

        return table

    def _resolve_hostname(self, ip: str) -> str:
        """Resolve IP to hostname."""
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ""

    def _guess_vendor(self, mac: str) -> str:
        """Guess device vendor from MAC OUI prefix."""
        oui = mac[:8].upper().replace(":", "-")
        oui_map = {
            "00-1A-2B": "Apple", "AC-DE-48": "Apple", "A4-83-E7": "Apple",
            "F0-18-98": "Apple", "3C-22-FB": "Apple",
            "B8-27-EB": "Raspberry Pi", "DC-A6-32": "Raspberry Pi",
            "00-50-56": "VMware", "00-0C-29": "VMware",
            "00-1B-44": "Samsung", "8C-F5-A3": "Samsung",
            "70-5A-0F": "HP", "3C-D9-2B": "HP",
            "D4-6E-0E": "TP-Link", "50-C7-BF": "TP-Link",
            "00-17-88": "Philips Hue",
        }
        return oui_map.get(oui, "Unknown")

    def _guess_device_type(self, device: NetworkDevice) -> str:
        """Guess device type from available info."""
        if device.is_gateway:
            return "router"
        hostname = device.hostname.lower()
        vendor = device.vendor.lower()
        if any(k in hostname for k in ["iphone", "android", "pixel", "galaxy"]):
            return "phone"
        if any(k in hostname for k in ["printer", "hp-", "epson"]):
            return "printer"
        if any(k in hostname for k in ["camera", "cam", "ipcam"]):
            return "camera"
        if "raspberry" in vendor:
            return "iot"
        if any(k in hostname for k in ["server", "nas", "synology"]):
            return "server"
        if any(k in hostname for k in ["tv", "roku", "chromecast", "firestick"]):
            return "tv"
        return "desktop" if device.hostname else "unknown"

    def _quick_port_scan(self, ip: str) -> list:
        """Quick scan of common ports."""
        open_ports = []
        for port in [22, 80, 443, 445, 631, 3389, 8080]:
            if is_port_open(ip, port, timeout=0.5):
                service = COMMON_PORTS.get(port, f"port-{port}")
                open_ports.append({"port": port, "service": service})
        return open_ports

    def print_map(self, devices: list):
        """Print a beautiful network map."""
        tree = Tree(f"[bold cyan]🌐 Network Map ({self.subnet})[/]")

        gateway = None
        others = []
        for d in devices:
            if d.is_gateway:
                gateway = d
            elif d.ip != self.local_ip:
                others.append(d)

        if gateway:
            gw_label = f"[bold green]🌐 Gateway ({gateway.ip})[/] - {gateway.vendor}"
            gw_node = tree.add(gw_label)
        else:
            gw_node = tree

        self_label = f"[bold cyan]💻 This Machine ({self.local_ip})[/]"
        gw_node.add(self_label)

        for d in others:
            icon = DEVICE_ICONS.get(d.device_type, "❓")
            name = d.hostname or d.device_type.title()
            ports_str = ""
            if d.open_ports:
                services = [p["service"] for p in d.open_ports[:3]]
                ports_str = f" [{', '.join(services)}]"
            color = "yellow" if d.device_type == "unknown" else "white"
            label = f"[{color}]{icon} {name} ({d.ip})[/] - {d.vendor}{ports_str}"
            gw_node.add(label)

        console.print(tree)
        console.print(f"\n[dim]Found {len(devices)} devices[/]")

        unknown = [d for d in devices if d.device_type == "unknown" and d.ip != self.local_ip]
        if unknown:
            console.print(f"[yellow]⚠️  {len(unknown)} unknown device(s) detected[/]")
