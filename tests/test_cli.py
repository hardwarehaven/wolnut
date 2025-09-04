import pytest
from click.testing import CliRunner

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


def test_wolnut_cli_with_config_file_arg(runner, mocker):
    """Tests passing a config file via command-line argument."""
    mock_main = mocker.patch("wolnut.cli.main")
    mocker.patch("wolnut.cli.os.path.exists", return_value=True)

    result = runner.invoke(wolnut, ["--config-file", "/test/config.yaml"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with("/test/config.yaml", None, False)


def test_wolnut_cli_with_env_var(runner, mocker):
    """Tests passing a config file via environment variable."""
    mock_main = mocker.patch("wolnut.cli.main")
    mocker.patch(
        "wolnut.cli.os.path.exists", return_value=False
    )  # Ensure default paths aren't found

    result = runner.invoke(
        wolnut,
        env={"WOLNUT_CONFIG_FILE": "/env/config.yaml"},
    )

    assert result.exit_code == 0
    mock_main.assert_called_once_with("/env/config.yaml", None, False)


def test_wolnut_cli_finds_default_config(runner, mocker):
    """Tests that the CLI finds a default config file path."""
    mock_main = mocker.patch("wolnut.cli.main")
    # Simulate the first default path not existing, but the second one does.
    mocker.patch("wolnut.cli.os.path.exists", side_effect=[False, True])

    result = runner.invoke(wolnut)

    assert result.exit_code == 0
    # Assumes the second default path is './config.yaml'
    mock_main.assert_called_once_with("./config.yaml", None, False)


def test_wolnut_cli_all_args(runner, mocker):
    """Tests that all CLI arguments are passed to main correctly."""
    mock_main = mocker.patch("wolnut.cli.main")
    mocker.patch("wolnut.cli.os.path.exists", return_value=True)

    result = runner.invoke(
        wolnut,
        ["--config-file", "a.yaml", "--status-file", "b.json", "--verbose"],
    )

    assert result.exit_code == 0
    mock_main.assert_called_once_with("a.yaml", "b.json", True)


def test_wolnut_cli_status_file_env_var(runner, mocker):
    """Tests passing a status file via environment variable."""
    mock_main = mocker.patch("wolnut.cli.main")
    mocker.patch("wolnut.cli.os.path.exists", side_effect=[True])  # Find default config

    result = runner.invoke(
        wolnut,
        env={"WOLNUT_STATUS_FILE": "/env/status.json"},
    )

    assert result.exit_code == 0
    # The default config file path will be found and used
    mock_main.assert_called_once_with("/config/config.yaml", "/env/status.json", False)


def test_wolnut_cli_no_args_no_default_config(runner, mocker):
    """Tests CLI when no arguments are given and no default config exists."""
    mocker.patch("wolnut.cli.os.path.exists", return_value=False)
    result = runner.invoke(wolnut)
    assert "No config file found." in result.stdout
    assert result.exit_code == 1
