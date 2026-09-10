"""Network utility functions."""
import socket
import struct
import subprocess
import platform


def get_local_ip() -> str:
    """Get this machine's local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_gateway() -> str:
    """Get the default gateway IP."""
    try:
        import netifaces
        gateways = netifaces.gateways()
        return gateways["default"][netifaces.AF_INET][0]
    except Exception:
        return "192.168.1.1"


def get_subnet(ip: str = None, prefix: int = 24) -> str:
    """Calculate subnet from IP address."""
    if ip is None:
        ip = get_local_ip()
    parts = ip.split(".")
    parts[-1] = "0"
    return f"{'.'.join(parts)}/{prefix}"


def ping(host: str, timeout: int = 2) -> dict:
    """Ping a host and return result with latency."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        output = subprocess.run(
            ["ping", param, "1", "-W", str(timeout), host],
            capture_output=True, text=True, timeout=timeout + 2
        )
        alive = output.returncode == 0
        latency = None
        if alive:
            for line in output.stdout.split("\n"):
                if "time=" in line or "time<" in line:
                    part = line.split("time=")[-1].split("time<")[-1]
                    latency = float(part.split("ms")[0].strip())
                    break
        return {"host": host, "alive": alive, "latency_ms": latency}
    except Exception:
        return {"host": host, "alive": False, "latency_ms": None}


def resolve_hostname(ip: str) -> str:
    """Reverse DNS lookup."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def is_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False
