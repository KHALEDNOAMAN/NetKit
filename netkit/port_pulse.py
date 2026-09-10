"""PortPulse - Service Health Monitor."""
import os
import time
import ssl
import socket
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box

import httpx
import yaml

console = Console()


@dataclass
class ServiceConfig:
    name: str
    type: str = "http"
    url: str = ""
    host: str = ""
    port: int = 0
    expected_status: int = 200
    timeout: int = 5


@dataclass
class ServiceResult:
    name: str
    is_healthy: bool = False
    response_time_ms: float = 0
    status_code: int = 0
    error: str = ""
    ssl_days_remaining: int = -1
    checked_at: str = ""
    uptime_pct: float = 100.0


class PortPulse:
    def __init__(self, config_path: str = "portpulse.yml"):
        self.config_path = config_path
        self.services = self._load_config()
        self.history = {}

    def _load_config(self) -> list:
        """Load service configuration from YAML."""
        if not os.path.exists(self.config_path):
            console.print(f"[yellow]Config not found: {self.config_path}[/]")
            console.print("Create portpulse.yml with your services. See README for format.")
            return []

        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        services = []
        for svc in data.get("services", []):
            services.append(ServiceConfig(
                name=svc.get("name", "Unknown"),
                type=svc.get("type", "http"),
                url=svc.get("url", ""),
                host=svc.get("host", ""),
                port=svc.get("port", 0),
                expected_status=svc.get("expected_status", 200),
                timeout=svc.get("timeout", 5),
            ))
        return services

    def check_service(self, svc: ServiceConfig) -> ServiceResult:
        """Check a single service."""
        result = ServiceResult(
            name=svc.name,
            checked_at=datetime.now().isoformat(),
        )

        try:
            if svc.type == "http":
                result = self._check_http(svc, result)
            elif svc.type == "tcp":
                result = self._check_tcp(svc, result)
            else:
                result.error = f"Unknown type: {svc.type}"
        except Exception as e:
            result.is_healthy = False
            result.error = str(e)

        # Update history for uptime calculation
        if svc.name not in self.history:
            self.history[svc.name] = []
        self.history[svc.name].append(result.is_healthy)
        checks = self.history[svc.name][-100:]
        result.uptime_pct = (sum(checks) / len(checks)) * 100

        return result

    def _check_http(self, svc: ServiceConfig, result: ServiceResult) -> ServiceResult:
        """Check HTTP service."""
        start = time.time()
        try:
            with httpx.Client(timeout=svc.timeout, verify=False) as client:
                resp = client.get(svc.url)
                result.response_time_ms = (time.time() - start) * 1000
                result.status_code = resp.status_code
                result.is_healthy = resp.status_code == svc.expected_status

                # Check SSL if HTTPS
                if svc.url.startswith("https://"):
                    result.ssl_days_remaining = self._check_ssl(
                        svc.url.split("://")[1].split("/")[0]
                    )
        except Exception as e:
            result.response_time_ms = (time.time() - start) * 1000
            result.is_healthy = False
            result.error = str(e)[:50]
        return result

    def _check_tcp(self, svc: ServiceConfig, result: ServiceResult) -> ServiceResult:
        """Check TCP port."""
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(svc.timeout)
            code = sock.connect_ex((svc.host, svc.port))
            result.response_time_ms = (time.time() - start) * 1000
            result.is_healthy = code == 0
            if not result.is_healthy:
                result.error = "Connection refused"
            sock.close()
        except Exception as e:
            result.response_time_ms = (time.time() - start) * 1000
            result.is_healthy = False
            result.error = str(e)[:50]
        return result

    def _check_ssl(self, hostname: str) -> int:
        """Check SSL certificate expiry days."""
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
                s.settimeout(5)
                s.connect((hostname, 443))
                cert = s.getpeercert()
                expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                return (expires - datetime.utcnow()).days
        except Exception:
            return -1

    def check_all(self) -> list:
        """Check all configured services."""
        results = []
        for svc in self.services:
            results.append(self.check_service(svc))
        return results

    def watch(self, interval: int = 30):
        """Continuous monitoring with live dashboard."""
        console.print(f"[cyan]Monitoring {len(self.services)} services (every {interval}s)...[/]")
        console.print("[dim]Press Ctrl+C to stop[/]\n")
        try:
            while True:
                results = self.check_all()
                console.clear()
                self.print_dashboard(results)
                console.print(f"\n[dim]Next check in {interval}s... (Ctrl+C to stop)[/]")
                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped.[/]")

    def print_dashboard(self, results: list):
        """Print service status dashboard."""
        table = Table(
            title="PortPulse Dashboard",
            box=box.ROUNDED,
            border_style="cyan",
            header_style="bold cyan",
        )
        table.add_column("Status", width=6, justify="center")
        table.add_column("Service", min_width=15)
        table.add_column("Response", justify="right", width=10)
        table.add_column("Uptime", justify="right", width=8)
        table.add_column("SSL", justify="right", width=8)
        table.add_column("Details", min_width=15)

        for r in results:
            status = "[green]● UP[/]" if r.is_healthy else "[red]● DOWN[/]"
            latency = f"{r.response_time_ms:.0f}ms" if r.is_healthy else "---"
            uptime = f"{r.uptime_pct:.1f}%"
            uptime_color = "green" if r.uptime_pct > 99 else "yellow" if r.uptime_pct > 95 else "red"

            ssl_str = ""
            if r.ssl_days_remaining >= 0:
                ssl_color = "green" if r.ssl_days_remaining > 30 else "yellow" if r.ssl_days_remaining > 7 else "red"
                ssl_str = f"[{ssl_color}]{r.ssl_days_remaining}d[/]"

            detail = r.error if r.error else f"HTTP {r.status_code}" if r.status_code else ""

            table.add_row(
                status, r.name, latency,
                f"[{uptime_color}]{uptime}[/]",
                ssl_str, detail
            )

        healthy = sum(1 for r in results if r.is_healthy)
        console.print(table)
        console.print(f"\n  [bold]{healthy}/{len(results)}[/] services healthy")
