"""
Comprehensive test for all client types in the tagged union
"""

from wolnut.client import (
    IdracClientConfig,
    IloClientConfig,
    IpmiClientConfig,
    WolClientConfig,
)
from wolnut.config import create_client_config


def test_wol_client():
    # Test WOL client
    wol_data = {
        "name": "WOL Server",
        "type": "wol",
        "host": "192.168.1.100",
        "mac": "aa:bb:cc:dd:ee:ff",
    }
    wol_client = create_client_config(wol_data)
    assert isinstance(wol_client, WolClientConfig)
    assert wol_client.type == "wol"


def test_idrac_client():
    # Test iDRAC client
    idrac_data = {
        "name": "Dell iDRAC Server",
        "type": "idrac",
        "host": "192.168.1.101",
        "ipmi_host": "192.168.1.102",
        "username": "admin",
        "password": "secret",
        "verify_ssl": False,
    }
    idrac_client = create_client_config(idrac_data)
    assert isinstance(idrac_client, IdracClientConfig)
    assert idrac_client.type == "idrac"


def test_ilo_client():
    # Test iLO client
    ilo_data = {
        "name": "HP iLO Server",
        "type": "ilo",
        "host": "192.168.1.103",
        "ipmi_host": "192.168.1.104",
        "username": "admin",
        "password": "secret",
        "verify_ssl": True,
    }
    ilo_client = create_client_config(ilo_data)
    assert isinstance(ilo_client, IloClientConfig)
    assert ilo_client.type == "ilo"


def test_ipmi_client():
    # Test IPMI client
    ipmi_data = {
        "name": "IPMI Server",
        "type": "ipmi",
        "host": "192.168.1.105",
        "ipmi_host": "192.168.1.106",
        "username": "admin",
        "password": "secret",
    }
    ipmi_client = create_client_config(ipmi_data)
    assert isinstance(ipmi_client, IpmiClientConfig)
    assert ipmi_client.type == "ipmi"
