"""
Test script to verify the configuration can be loaded from YAML
"""

import os
import tempfile

import yaml

from wolnut.client import (
    IdracClientConfig,
    IloClientConfig,
    SmIpmiClientConfig,
    WolClientConfig,
)
from wolnut.config import NutConfig, WakeOnConfig, WolnutConfig, load_config


def test_config_loading():
    # Create a temporary config file
    test_config = {
        "log_level": "INFO",
        "nut": {"ups": "ups@localhost", "username": "upsmon", "password": "password"},
        "poll_interval": 15,
        "wake_on": {
            "restore_delay_sec": 30,
            "min_battery_percent": 25,
            "client_timeout_sec": 600,
            "reattempt_delay": 30,
        },
        "clients": [
            {
                "name": "Server A",
                "type": "wol",
                "host": "192.168.0.100",
                "mac": "aa:bb:cc:dd:ee:ff",
            },
            # { # can't resolve MAC during tests
            #     "name": "Server B",
            #     "type": "wol",
            #     "host": "192.168.0.101",
            #     "mac": "auto",
            # },
            {
                "name": "Server C",
                "host": "192.168.0.102",
                "mac": "aa:bb:cc:dd:ee:ff",
            },
            {
                "name": "Dell iDRAC Server",
                "type": "idrac",
                "host": "server.local",
                "ipmi_host": "192.168.0.203",
                "username": "root",
                "password": "calvin",
                "verify_ssl": True,
            },
            {
                "name": "Supermicro Server",
                "type": "sm_ipmi",
                "host": "192.168.0.104",
                "ipmi_host": "192.168.0.204",
                "username": "admin",
                "password": "admin",
            },
            {
                "name": "HP iLO Server",
                "type": "ilo",
                "host": "192.168.0.105",
                "ipmi_host": "192.168.0.205",
                "username": "admin",
                "password": "admin",
                "verify_ssl": False,
            },
        ],
    }

    expected = WolnutConfig(
        nut=NutConfig(ups="ups@localhost", username="upsmon", password="password"),
        poll_interval=15,
        wake_on=WakeOnConfig(
            restore_delay_sec=30,
            min_battery_percent=25,
            client_timeout_sec=600,
            reattempt_delay=30,
        ),
        clients=[
            WolClientConfig(
                name="Server A", host="192.168.0.100", mac="aa:bb:cc:dd:ee:ff"
            ),
            # WolClientConfig(name="Server B", host="192.168.0.101", mac="auto"), # can't resolve MAC during tests
            WolClientConfig(
                name="Server C", host="192.168.0.102", mac="aa:bb:cc:dd:ee:ff"
            ),
            IdracClientConfig(
                name="Dell iDRAC Server",
                host="server.local",
                ipmi_host="192.168.0.203",
                username="root",
                password="calvin",
                verify_ssl=True,
            ),
            SmIpmiClientConfig(
                name="Supermicro Server",
                host="192.168.0.104",
                ipmi_host="192.168.0.204",
                username="admin",
                password="admin",
            ),
            IloClientConfig(
                name="HP iLO Server",
                host="192.168.0.105",
                ipmi_host="192.168.0.205",
                username="admin",
                password="admin",
                verify_ssl=False,
            ),
        ],
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_config, f)
        temp_config_path = f.name

    try:
        # Load the config
        config = load_config(temp_config_path)

        assert config == expected, f"Config does not match expected structure: {config}"
    finally:
        # Clean up
        os.unlink(temp_config_path)
