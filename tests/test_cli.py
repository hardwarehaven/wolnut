import pytest
from click.testing import CliRunner

from wolnut import main
from wolnut.cli import wolnut, get_battery_percent


@pytest.fixture
def runner():
    return CliRunner()


def test_get_battery_percent():
    """Tests the battery percentage parsing function."""
    assert get_battery_percent({"battery.charge": "95.5"}) == 96
    assert get_battery_percent({"battery.charge": "20"}) == 20
    assert get_battery_percent({}) == 100
    assert get_battery_percent({"some_other_key": "value"}) == 100


def test_wolnut_cli_no_config(runner, mocker):
    """Tests the CLI response when no config file is found."""
    mocker.patch("wolnut.cli.os.path.exists", return_value=False)
    result = runner.invoke(wolnut)
    assert "No config file found." in result.stdout
    assert result.exit_code == 1


def test_wolnut_cli_verbose_flag(runner, mocker):
    """Tests that the --verbose flag sets the log level to DEBUG."""
    mock_main = mocker.patch("wolnut.cli.main", return_value=0)
    mocker.patch("wolnut.cli.os.path.exists", return_value=True)
    mock_configure_logger = mocker.patch(
        "wolnut.cli.configure_logger"
    )  # This will now work

    # The main function is mocked, so we don't need to mock load_config.
    # The logger configuration happens in the `wolnut` CLI function itself.

    result = runner.invoke(wolnut, ["--verbose"])

    assert result.exit_code == 0
    # The verbose flag should set the log level to DEBUG before main is called.
    mock_configure_logger.assert_called_once_with("DEBUG")
    # And main should be called with verbose=True
    mock_main.assert_called_once_with("/config/config.yaml", None, True)


def test_wolnut_cli_with_config_file_arg(runner, mocker):
    """Tests passing a config file via command-line argument."""
    mock_main = mocker.patch("wolnut.cli.main", return_value=0)
    mocker.patch("wolnut.cli.os.path.exists", return_value=True)

    result = runner.invoke(wolnut, ["--config-file", "/test/config.yaml"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with("/test/config.yaml", None, False)


def test_wolnut_cli_with_env_var(runner, mocker):
    """Tests passing a config file via environment variable."""
    mock_main = mocker.patch("wolnut.cli.main", return_value=0)
    mocker.patch("wolnut.cli.os.path.exists", return_value=False)

    result = runner.invoke(
        wolnut,
        env={"WOLNUT_CONFIG_FILE": "/env/config.yaml"},
    )

    assert result.exit_code == 0
    mock_main.assert_called_once_with("/env/config.yaml", None, False)


def test_wolnut_cli_finds_default_config(runner, mocker):
    """Tests that the CLI finds a default config file path."""
    mock_main = mocker.patch("wolnut.cli.main", return_value=0)
    # Simulate the first default path not existing, but the second one does.
    mocker.patch("wolnut.cli.os.path.exists", side_effect=[False, True])

    result = runner.invoke(wolnut)

    assert result.exit_code == 0
    # Assumes the second default path is './config.yaml'
    mock_main.assert_called_once_with("./config.yaml", None, False)


def test_wolnut_cli_all_args(runner, mocker):
    """Tests that all CLI arguments are passed to main correctly."""
    mock_main = mocker.patch("wolnut.cli.main", return_value=0)
    mocker.patch("wolnut.cli.os.path.exists", return_value=True)

    result = runner.invoke(
        wolnut,
        ["--config-file", "a.yaml", "--status-file", "b.json", "--verbose"],
    )

    assert result.exit_code == 0
    mock_main.assert_called_once_with("a.yaml", "b.json", True)


def test_wolnut_cli_status_file_env_var(runner, mocker):
    """Tests passing a status file via environment variable."""
    mock_main = mocker.patch("wolnut.cli.main", return_value=0)
    mocker.patch("wolnut.cli.os.path.exists", side_effect=[True])  # Find default config

    result = runner.invoke(
        wolnut,
        env={"WOLNUT_STATUS_FILE": "/env/status.json"},
    )

    assert result.exit_code == 0
    # The default config file path will be found and used
    mock_main.assert_called_once_with("/config/config.yaml", "/env/status.json", False)
