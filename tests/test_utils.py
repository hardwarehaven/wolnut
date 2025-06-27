import utils
import subprocess


def test_validate_mac_format():
    valid_mac_address = "de:ad:be:ef:be:ad"
    invalid_mac_address = "ea:ts:be:ef:be:ad"  # Mmm. Delicious beef bead.

    # `validate_mac_format()` returns a bool, so no need to compare with `==`
    assert utils.validate_mac_format(valid_mac_address)
    assert not utils.validate_mac_format(invalid_mac_address)


def test_resolve_mac_from_host(mocker):
    # [ TODO - Issue #24 ] - Write tests that assert the appropriate exceptions were raised
    class MockSubprocessResultOkay(object):
        stdout = "de:ad:be:ef:be:ad"

    mock_subprocess_run = mocker.patch("utils.subprocess.run")
    mock_subprocess_run.return_value = MockSubprocessResultOkay()
    result = utils.resolve_mac_from_host("localhost")
    assert result == MockSubprocessResultOkay.stdout
    mock_subprocess_run.assert_any_call(
        ["ping", "-c", "1", "localhost"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    mock_subprocess_run.assert_any_call(
        ["arp", "-n", "localhost"], capture_output=True, text=True
    )
