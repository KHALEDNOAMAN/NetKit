"""NetKit CLI - One tool, three network diagnostic powers."""
import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="NetKit")
def main():
    """NetKit - Network Diagnostic Toolkit

    One tool, three network diagnostic powers:
    WiFi analysis, device discovery, and service monitoring.
    """
    pass


@main.command()
@click.option("--interface", "-i", default=None, help="Network interface to use")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def wifi(interface, json_output):
    """Diagnose WiFi issues - channels, signal, DNS speed."""
    from netkit.wifi_doctor import WifiDoctor

    doctor = WifiDoctor(interface=interface)
    report = doctor.diagnose()
    if json_output:
        import json
        console.print(json.dumps(report, indent=2))
    else:
        doctor.print_report(report)


@main.command()
@click.option("--subnet", "-s", default=None, help="Subnet to scan (e.g. 192.168.1.0/24)")
@click.option("--timeout", "-t", default=3, help="Scan timeout in seconds")
def scan(subnet, timeout):
    """Discover all devices on your network."""
    from netkit.network_mapper import NetworkMapper

    mapper = NetworkMapper(subnet=subnet, timeout=timeout)
    devices = mapper.discover()
    mapper.print_map(devices)


@main.command()
@click.option("--config", "-c", default="portpulse.yml", help="Config file path")
@click.option("--watch", "-w", is_flag=True, help="Continuous monitoring mode")
@click.option("--interval", default=30, help="Check interval in seconds")
def monitor(config, watch, interval):
    """Monitor service health from config file."""
    from netkit.port_pulse import PortPulse

    pulse = PortPulse(config_path=config)
    if watch:
        pulse.watch(interval=interval)
    else:
        results = pulse.check_all()
        pulse.print_dashboard(results)


@main.command()
def report():
    """Generate a full network diagnostic report."""
    from netkit.wifi_doctor import WifiDoctor
    from netkit.network_mapper import NetworkMapper

    console.rule("[bold cyan]NetKit Full Diagnostic Report[/]")
    console.print()

    console.rule("[cyan]WiFi Analysis[/]")
    doctor = WifiDoctor()
    wifi_report = doctor.diagnose()
    doctor.print_report(wifi_report)

    console.print()
    console.rule("[cyan]Network Devices[/]")
    mapper = NetworkMapper()
    devices = mapper.discover()
    mapper.print_map(devices)

    console.print()
    console.print("[bold green]Report complete![/]")


if __name__ == "__main__":
    main()
