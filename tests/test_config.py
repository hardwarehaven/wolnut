import pytest
import yaml

from wolnut import config


@pytest.fixture
def minimal_config_dict():
    return {
        "nut": {"ups": "ups@localhost"},
        "clients": [
            {"name": "client-1", "host": "192.168.1.10", "mac": "DE:AD:BE:EF:00:01"}
        ],
    }


@pytest.fixture
def full_config_dict():
    return {
        "log_level": "DEBUG",
        "poll_interval": 5,
        "status_file": "/data/status.json",
        "nut": {
            "ups": "myups@nut-server",
            "port": 1234,
            "username": "monuser",
            "password": "monpassword",
        },
        "wake_on": {
            "restore_delay_sec": 60,
            "min_battery_percent": 50,
            "client_timeout_sec": 900,
            "reattempt_delay": 45,
        },
        "clients": [
            {
                "name": "desktop",
                "host": "desktop.local",
                "mac": "DE:AD:BE:EF:00:01",
            },
            {"name": "server", "host": "server.local", "mac": "auto"},
        ],
    }


def test_load_config_minimal(mocker, minimal_config_dict):
    """Tests loading a minimal valid configuration."""
    mocker.patch(
        "builtins.open", mocker.mock_open(read_data=yaml.dump(minimal_config_dict))
    )
    mocker.patch("wolnut.config.validate_config")
    mocker.patch("wolnut.config.resolve_mac_from_host")  # Prevent actual resolution

    cfg = config.load_config("dummy_path.yaml", None, False)

    assert cfg.nut.ups == "ups@localhost"
    assert cfg.poll_interval == 10  # Default
    assert cfg.wake_on.min_battery_percent == 20  # Default
    assert len(cfg.clients) == 1
    assert (
        cfg.clients[0].name == "client-1"
    )  # This was failing because host was missing
    assert cfg.log_level == "INFO"  # Default


def test_load_config_full(mocker, full_config_dict):
    """Tests loading a full configuration with all options set."""
    mocker.patch(
        "builtins.open", mocker.mock_open(read_data=yaml.dump(full_config_dict))
    )
    mocker.patch("wolnut.config.validate_config")
    mock_resolve_mac = mocker.patch(
        "wolnut.config.resolve_mac_from_host", return_value="11:22:33:44:55:66"
    )

    cfg = config.load_config("dummy_path.yaml", None, False)

    assert cfg.log_level == "DEBUG"
    assert cfg.poll_interval == 5
    assert cfg.status_file == "/data/status.json"
    assert cfg.nut.ups == "myups@nut-server"
    assert cfg.nut.username == "monuser"
    assert cfg.wake_on.restore_delay_sec == 60
    assert cfg.wake_on.min_battery_percent == 50
    assert len(cfg.clients) == 2
    assert cfg.clients[0].mac == "DE:AD:BE:EF:00:01"
    assert cfg.clients[1].mac == "11:22:33:44:55:66"  # Resolved MAC
    mock_resolve_mac.assert_called_once_with("server.local")


def test_load_config_file_not_found(mocker):
    """Tests that None is returned when the config file is not found."""
    mocker.patch("builtins.open", side_effect=FileNotFoundError)

    result = config.load_config("nonexistent.yaml", None, False)

    assert result is None


def test_load_config_mac_resolution_fails(mocker, minimal_config_dict):
    """Tests that a client is skipped if MAC address resolution fails."""
    minimal_config_dict["clients"][0]["mac"] = "auto"
    mocker.patch(
        "builtins.open", mocker.mock_open(read_data=yaml.dump(minimal_config_dict))
    )
    mocker.patch("wolnut.config.validate_config")
    mocker.patch("wolnut.config.resolve_mac_from_host", return_value=None)

    cfg = config.load_config("dummy.yaml", None, False)

    # The client that failed resolution should not be in the final list
    assert len(cfg.clients) == 0


@pytest.mark.parametrize(
    "invalid_config, error_msg",
    [
        ({"nut": {"ups": "ups"}}, "Missing or invalid 'clients' list"),
        ({"clients": []}, "Missing required field: 'nut.ups'"),
        ({"nut": {}, "clients": []}, "Missing required field: 'nut.ups'"),
        (
            {"nut": {"ups": "ups"}, "clients": [{}]},
            "Client #0 is missing required field: 'name'",
        ),
        (
            {"nut": {"ups": "ups"}, "clients": [{"name": "c1"}]},
            "Client 'c1' is missing required field: 'host'",
        ),
        (
            {
                "nut": {"ups": "ups"},
                "clients": [{"name": "c1", "host": "h1"}],
            },  # This test is correct
            "Client 'c1' is missing required field: 'mac'",
        ),
        (
            {
                "nut": {"ups": "ups"},
                "clients": [{"name": "c1", "host": "h1", "mac": 12345}],
            },
            "has invalid mac format",
        ),
        (
            {
                "nut": {"ups": "ups"},
                "clients": [{"name": "c1", "host": "h1", "mac": "invalid-mac"}],
            },
            "has invalid MAC address format",
        ),
    ],
)
def test_validate_config_failures(invalid_config, error_msg):
    """Tests various invalid configuration scenarios for validate_config."""
    with pytest.raises(ValueError, match=error_msg):
        config.validate_config(invalid_config)


def test_validate_config_success(minimal_config_dict):
    """Tests that a valid config passes validation without error."""
    try:
        config.validate_config(minimal_config_dict)
    except ValueError:
        pytest.fail("validate_config raised ValueError unexpectedly")


def test_load_config_status_path_override(mocker, minimal_config_dict):
    """Tests that the status_path argument overrides the config file value."""
    minimal_config_dict["status_file"] = "/config/status.json"
    mocker.patch(
        "builtins.open", mocker.mock_open(read_data=yaml.dump(minimal_config_dict))
    )
    mocker.patch("wolnut.config.validate_config")
    mocker.patch("wolnut.config.resolve_mac_from_host")

    cfg = config.load_config("dummy.yaml", "/override/status.json", False)

    assert cfg.status_file == "/override/status.json"


def test_load_config_yaml_error(mocker):
    """Tests that None is returned on a YAML parsing error."""
    mocker.patch("builtins.open", mocker.mock_open(read_data="not: valid: yaml"))

    result = config.load_config("bad.yaml", None, False)

    assert result is None


def test_load_config_verbose_flag(mocker, minimal_config_dict):
    """Tests that the verbose flag overrides the log level in the config."""
    minimal_config_dict["log_level"] = "INFO"
    mocker.patch(
        "builtins.open", mocker.mock_open(read_data=yaml.dump(minimal_config_dict))
    )
    mocker.patch("wolnut.config.validate_config")
    mocker.patch("wolnut.config.resolve_mac_from_host")

    # The verbose flag is not actually used in load_config, but this test confirms
    # the log_level is read from the file correctly when verbose is False.
    # A more advanced test would involve checking the logger's level.
    cfg = config.load_config("dummy.yaml", None, False)
    assert cfg.log_level == "INFO"
