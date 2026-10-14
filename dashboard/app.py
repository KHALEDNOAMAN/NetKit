"""NetKit Web Dashboard - Real-time network monitoring."""
import json
import os
from flask import Flask, render_template, jsonify
from netkit.wifi_doctor import WifiDoctor
from netkit.network_mapper import NetworkMapper
from netkit.port_pulse import PortPulse

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/wifi")
def api_wifi():
    doctor = WifiDoctor()
    report = doctor.diagnose()
    return jsonify(report)


@app.route("/api/devices")
def api_devices():
    mapper = NetworkMapper()
    devices = mapper.discover()
    return jsonify([{
        "ip": d.ip, "mac": d.mac, "hostname": d.hostname,
        "vendor": d.vendor, "type": d.device_type,
        "is_gateway": d.is_gateway,
        "ports": d.open_ports,
    } for d in devices])


@app.route("/api/services")
def api_services():
    pulse = PortPulse()
    if not pulse.services:
        return jsonify([])
    results = pulse.check_all()
    return jsonify([{
        "name": r.name, "healthy": r.is_healthy,
        "response_ms": round(r.response_time_ms, 1),
        "uptime_pct": r.uptime_pct,
        "ssl_days": r.ssl_days_remaining,
        "error": r.error,
    } for r in results])


if __name__ == "__main__":
    # Flask debug serves the Werkzeug console, which executes arbitrary
    # Python in the browser. On 0.0.0.0 that is remote code execution for
    # anyone who can reach the port, so neither is a default here.
    host = os.environ.get("NETKIT_HOST", "127.0.0.1")
    port = int(os.environ.get("NETKIT_PORT", "5000"))
    debug = os.environ.get("NETKIT_DEBUG", "").lower() in ("1", "true", "yes")
    if debug and host != "127.0.0.1":
        raise SystemExit(
            "refusing to run the debug console on a non loopback address"
        )
    app.run(host=host, port=port, debug=debug)
