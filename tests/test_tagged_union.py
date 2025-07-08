#!/usr/bin/env python3
"""
Test script to verify the tagged union configuration works correctly
"""

from wolnut.client import IdracClientConfig, WolClientConfig, create_client_config


def test_tagged_union():
    # Test WOL client
    wol_data = {
        "name": "Test WOL",
        "type": "wol",
        "host": "192.168.1.100",
        "mac": "aa:bb:cc:dd:ee:ff",
    }

    wol_client = create_client_config(wol_data)
    print(f"WOL Client: {wol_client}")
    assert isinstance(wol_client, WolClientConfig)
    assert wol_client.name == "Test WOL"
    assert wol_client.type == "wol"
    assert wol_client.mac == "aa:bb:cc:dd:ee:ff"

    # Test iDRAC client
    idrac_data = {
        "name": "Test iDRAC",
        "type": "idrac",
        "host": "192.168.1.101",
        "ipmi_host": "192.168.1.102",
        "username": "admin",
        "password": "secret",
        "verify_ssl": False,
    }

    idrac_client = create_client_config(idrac_data)
    print(f"iDRAC Client: {idrac_client}")
    assert isinstance(idrac_client, IdracClientConfig)
    assert idrac_client.name == "Test iDRAC"
    assert idrac_client.host == "192.168.1.101"
    assert idrac_client.ipmi_host == "192.168.1.102"
    assert idrac_client.username == "admin"
    assert idrac_client.password == "secret"
    assert idrac_client.verify_ssl == False

    # Test backward compatibility - clients can still be accessed uniformly
    clients = [wol_client, idrac_client]

    for client in clients:
        print(f"Client: {client.name}, Type: {client.type}, Host: {client.host}")
        # Type-specific access
        if client.type == "wol":
            print(f"  WOL MAC: {client.mac}")
        elif client.type == "idrac":
            print(f"  iDRAC IPMI: {client.host}")
