"""Tests for NetKit utility functions."""
import pytest
from netkit.utils import get_local_ip, get_subnet, is_port_open


def test_get_local_ip():
    ip = get_local_ip()
    assert ip is not None
    assert ip.count(".") == 3
    assert ip != "0.0.0.0"


def test_get_subnet():
    subnet = get_subnet("192.168.1.100")
    assert subnet == "192.168.1.0/24"


def test_get_subnet_custom_prefix():
    subnet = get_subnet("10.0.0.50", prefix=16)
    assert subnet == "10.0.0.0/16"


def test_is_port_open_closed():
    result = is_port_open("127.0.0.1", 59999, timeout=0.5)
    assert result is False


def test_is_port_open_timeout():
    result = is_port_open("192.0.2.1", 80, timeout=0.5)
    assert result is False
