"""NetKit configuration defaults."""

DEFAULT_CONFIG = {
    "wifi": {
        "channels_24ghz": [1, 6, 11],
        "signal_thresholds": {"excellent": 80, "good": 60, "fair": 40, "poor": 20},
        "dns_threshold_ms": 100,
    },
    "scan": {
        "timeout": 3,
        "common_ports": [22, 80, 443, 445, 631, 3389, 8080],
    },
    "monitor": {
        "interval": 30,
        "history_size": 100,
    },
}

COLORS = {
    "primary": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "info": "blue",
}
