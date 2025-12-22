from wolnut import utils
from unittest.mock import patch, Mock


def test_validate_mac_format():
    valid_mac_address = "de:ad:be:ef:be:ad"
    invalid_mac_address = "ea:ts:be:ef:be:ad"

    assert utils.validate_mac_format(valid_mac_address)
    assert not utils.validate_mac_format(invalid_mac_address)


def test_resolve_mac_from_host(mocker):
    # [ TODO - Issue #24 ] - Write tests that assert the appropriate exceptions were raised
    EXPECTED_RESULT = "de:ad:be:ef:be:ad"
    EXPECTED_HOST = "localhost"
    with patch("wolnut.utils.Popen", Mock()) as popen_mock:
        popen_mock().communicate.return_value = EXPECTED_RESULT
        popen_mock.call_args_list.clear()
        assert utils.resolve_mac_from_host(EXPECTED_HOST) == EXPECTED_RESULT
    assert len(popen_mock.call_args_list) == 2
    ping_call_args, arp_call_args = popen_mock.call_args_list
    command, *_ , destination = ping_call_args.args[0]
    assert (command, destination) == ("ping", EXPECTED_HOST)
    command, *_ , destination = arp_call_args.args[0]
    assert (command, destination) == ("arp", EXPECTED_HOST)