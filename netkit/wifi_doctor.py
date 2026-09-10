"""WiFi Doctor - Diagnose WiFi issues instantly."""
import socket
import time
import subprocess
import platform
from dataclasses import dataclass, field
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import box

from netkit.utils import get_local_ip, get_gateway, ping

console = Console()


@dataclass
class WifiNetwork:
    ssid: str
    bssid: str = ""
    channel: int = 0
    signal_strength: int = 0
    security: str = ""


@dataclass
class WifiReport:
    connected_ssid: str = ""
    signal_percent: int = 0
    channel: int = 0
    channel_congestion: int = 0
    recommended_channel: int = 0
    gateway_ip: str = ""
    gateway_latency_ms: float = 0.0
    dns_latency_ms: float = 0.0
    local_ip: str = ""
    nearby_networks: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


class WifiDoctor:
    DNS_SERVERS = ["1.1.1.1", "8.8.8.8", "9.9.9.9", "208.67.222.222"]

    def __init__(self, interface: Optional[str] = None):
        self.interface = interface

    def diagnose(self) -> dict:
        """Run full WiFi diagnosis."""
        report = WifiReport()
        report.local_ip = get_local_ip()
        report.gateway_ip = get_gateway()

        # Gateway latency
        gw_ping = ping(report.gateway_ip)
        report.gateway_latency_ms = gw_ping.get("latency_ms", 0) or 0

        # DNS latency
        report.dns_latency_ms = self._measure_dns_latency()

        # Scan nearby networks
        report.nearby_networks = self._scan_networks()
        report.signal_percent = self._estimate_signal()

        # Channel analysis
        if report.nearby_networks:
            channels = [n.channel for n in report.nearby_networks if n.channel > 0]
            if channels:
                report.channel = channels[0] if channels else 0
                channel_counts = {}
                for ch in channels:
                    channel_counts[ch] = channel_counts.get(ch, 0) + 1
                report.channel_congestion = channel_counts.get(report.channel, 0)
                best_ch, best_count = 0, 999
                for ch in [1, 6, 11]:
                    count = channel_counts.get(ch, 0)
                    if count < best_count:
                        best_ch, best_count = ch, count
                report.recommended_channel = best_ch

        # Generate issues and recommendations
        if report.gateway_latency_ms > 50:
            report.issues.append("High gateway latency")
            report.recommendations.append("Check router load or interference")
        if report.dns_latency_ms > 100:
            report.issues.append(f"Slow DNS response ({report.dns_latency_ms:.0f}ms)")
            report.recommendations.append("Switch DNS to 1.1.1.1 or 8.8.8.8")
        if report.channel_congestion > 5:
            report.issues.append(f"Channel {report.channel} is congested ({report.channel_congestion} networks)")
            report.recommendations.append(f"Switch router to Channel {report.recommended_channel}")
        if report.signal_percent < 50:
            report.issues.append("Weak signal strength")
            report.recommendations.append("Move closer to router or add a WiFi extender")

        return report.__dict__

    def _measure_dns_latency(self) -> float:
        """Measure DNS resolution latency."""
        best = 999.0
        for dns in self.DNS_SERVERS:
            try:
                start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((dns, 53))
                latency = (time.time() - start) * 1000
                sock.close()
                if latency < best:
                    best = latency
            except Exception:
                continue
        return round(best, 1)

    def _scan_networks(self) -> list:
        """Scan for nearby WiFi networks (platform-dependent)."""
        networks = []
        system = platform.system().lower()
        try:
            if system == "windows":
                output = subprocess.run(
                    ["netsh", "wlan", "show", "networks", "mode=Bssid"],
                    capture_output=True, text=True, timeout=10
                )
                current = None
                for line in output.stdout.split("\n"):
                    line = line.strip()
                    if line.startswith("SSID") and "BSSID" not in line:
                        ssid = line.split(":", 1)[-1].strip()
                        current = WifiNetwork(ssid=ssid)
                        networks.append(current)
                    elif current and "Channel" in line:
                        try:
                            current.channel = int(line.split(":")[-1].strip())
                        except ValueError:
                            pass
                    elif current and "Signal" in line:
                        try:
                            current.signal_strength = int(line.split(":")[-1].strip().replace("%", ""))
                        except ValueError:
                            pass
            elif system == "linux":
                output = subprocess.run(
                    ["iwlist", "scanning"], capture_output=True, text=True, timeout=10
                )
                current = None
                for line in output.stdout.split("\n"):
                    if "ESSID:" in line:
                        ssid = line.split('ESSID:"')[-1].rstrip('"')
                        current = WifiNetwork(ssid=ssid)
                        networks.append(current)
                    elif current and "Channel:" in line:
                        try:
                            current.channel = int(line.split("Channel:")[-1])
                        except ValueError:
                            pass
                    elif current and "Signal level" in line:
                        try:
                            dbm = int(line.split("Signal level=")[-1].split(" ")[0])
                            current.signal_strength = max(0, min(100, 2 * (dbm + 100)))
                        except (ValueError, IndexError):
                            pass
        except Exception:
            pass
        return networks

    def _estimate_signal(self) -> int:
        """Estimate current connection signal strength."""
        system = platform.system().lower()
        try:
            if system == "windows":
                output = subprocess.run(
                    ["netsh", "wlan", "show", "interfaces"],
                    capture_output=True, text=True, timeout=5
                )
                for line in output.stdout.split("\n"):
                    if "Signal" in line:
                        return int(line.split(":")[-1].strip().replace("%", ""))
            elif system == "linux":
                with open("/proc/net/wireless", "r") as f:
                    lines = f.readlines()
                    if len(lines) > 2:
                        parts = lines[2].split()
                        quality = float(parts[2].rstrip("."))
                        return int((quality / 70) * 100)
        except Exception:
            pass
        return 75  # Default estimate

    def print_report(self, report: dict):
        """Print a beautiful WiFi diagnosis report."""
        signal = report.get("signal_percent", 0)
        bars = "█" * (signal // 10) + "░" * (10 - signal // 10)
        quality = "Excellent" if signal > 80 else "Good" if signal > 60 else "Fair" if signal > 40 else "Poor"
        color = "green" if signal > 60 else "yellow" if signal > 40 else "red"

        panel_content = f"""[bold]Signal Strength:[/]  {bars}  {signal}% ([{color}]{quality}[/])
[bold]Local IP:[/]          {report.get('local_ip', 'N/A')}
[bold]Gateway:[/]           {report.get('gateway_ip', 'N/A')} ({report.get('gateway_latency_ms', 0):.0f}ms)
[bold]DNS Latency:[/]       {report.get('dns_latency_ms', 0):.0f}ms
[bold]Channel:[/]           {report.get('channel', 'N/A')} ({report.get('channel_congestion', 0)} networks)
[bold]Recommended:[/]       Channel {report.get('recommended_channel', 'N/A')}
[bold]Nearby Networks:[/]   {len(report.get('nearby_networks', []))}"""

        console.print(Panel(panel_content, title="📡 WiFi Health Report", border_style="cyan"))

        issues = report.get("issues", [])
        recs = report.get("recommendations", [])
        if issues:
            console.print("\n[bold red]Issues Found:[/]")
            for i, issue in enumerate(issues, 1):
                console.print(f"  {i}. ❌ {issue}")
        if recs:
            console.print("\n[bold green]Recommendations:[/]")
            for i, rec in enumerate(recs, 1):
                console.print(f"  {i}. 💡 {rec}")
        if not issues:
            console.print("\n[bold green]✅ No issues detected! WiFi looks healthy.[/]")
