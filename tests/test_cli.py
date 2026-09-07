import pytest
from click.testing import CliRunner

from wolnut import main
from wolnut.cli import wolnut, get_battery_percent
from wolnut.config import ClientConfig, NutConfig, WakeOnConfig, WolnutConfig
from wolnut.state import ClientStateTracker


@pytest.fixture
def runner():
    return CliRunner()


class LoopBreaker(Exception):
    """Raised from the patched time.sleep to break out of main()'s infinite loop."""


CLIENT = ClientConfig(name="client-1", host="192.168.1.10", mac="DE:AD:BE:EF:00:01")


def _make_config(status_file: str, reset_state_on_resume: bool) -> WolnutConfig:
    """Builds a config whose wake_on thresholds never delay a WOL attempt."""
    return WolnutConfig(
        nut=NutConfig(ups="ups@localhost"),
        status_file=status_file,
        poll_interval=1,
        wake_on=WakeOnConfig(
            restore_delay_sec=0,
            min_battery_percent=0,
            client_timeout_sec=600,
            reattempt_delay=0,
        ),
        clients=[CLIENT],
        reset_state_on_resume=reset_state_on_resume,
    )


def _write_post_outage_state(status_file: str):
    """
    Writes the state file exactly as wolnut would have left it if it was killed by
    a power outage: the client was online, got snapshotted when the UPS went to
    battery, and then went offline.
    """
    tracker = ClientStateTracker([CLIENT], status_file=status_file)
    tracker.update(CLIENT.name, True)
    tracker.mark_all_online_clients()
    tracker.set_ups_on_battery(True, 55)
    tracker.update(CLIENT.name, False)
    tracker.save_state()

    # Sanity check: the state we just persisted is what a fresh process would load.
    reloaded = ClientStateTracker([CLIENT], status_file=status_file)
    assert reloaded.was_ups_on_battery()
    assert reloaded.was_online_before_shutdown(CLIENT.name)


def _run_main_once(mocker, tmp_path, reset_state_on_resume: bool):
    """
    Simulates wolnut restarting on a freshly-booted host after an outage, with the
    UPS already back on line power, and returns the send_wol_packet mock.
    """
    status_file = str(tmp_path / "wolnut_state.json")
    _write_post_outage_state(status_file)

    mocker.patch(
        "wolnut.cli.load_config",
        return_value=_make_config(status_file, reset_state_on_resume),
    )
    mocker.patch(
        "wolnut.cli.get_ups_status",
        return_value={"ups.status": "OL", "battery.charge": "100"},
    )
    mocker.patch("wolnut.cli.is_client_online", return_value=False)
    mock_send_wol = mocker.patch("wolnut.cli.send_wol_packet", return_value=True)
    # Break out of the main loop at the end of the first iteration.
    mocker.patch("wolnut.cli.time.sleep", side_effect=LoopBreaker)

    with pytest.raises(LoopBreaker):
        main("dummy.yaml", status_file, False)

    return mock_send_wol


def test_resume_with_reset_state_on_resume_true_sends_no_wol(mocker, tmp_path):
    """
    Default behaviour (unchanged): the saved state is discarded on resume, so no
    client is considered to have been online before the outage and nothing is woken.
    """
    mock_send_wol = _run_main_once(mocker, tmp_path, reset_state_on_resume=True)

    mock_send_wol.assert_not_called()


def test_resume_with_reset_state_on_resume_false_sends_wol(mocker, tmp_path):
    """
    Regression test: with reset_state_on_resume disabled, a client that was online
    before the outage is still eligible for WOL after wolnut restarts.
    """
    mock_send_wol = _run_main_once(mocker, tmp_path, reset_state_on_resume=False)

    mock_send_wol.assert_called_once_with(CLIENT.mac)


def test_resume_with_reset_state_on_resume_false_does_not_reset_tracker(
    mocker, tmp_path
):
    """The loaded state must survive startup untouched when the option is disabled."""
    status_file = str(tmp_path / "wolnut_state.json")
    _write_post_outage_state(status_file)

    mocker.patch(
        "wolnut.cli.load_config",
        return_value=_make_config(status_file, reset_state_on_resume=False),
    )
    mocker.patch(
        "wolnut.cli.get_ups_status",
        return_value={"ups.status": "OL", "battery.charge": "100"},
    )
    mocker.patch("wolnut.cli.is_client_online", return_value=False)
    mocker.patch("wolnut.cli.send_wol_packet", return_value=True)
    mock_reset = mocker.patch.object(ClientStateTracker, "reset")
    mocker.patch("wolnut.cli.time.sleep", side_effect=LoopBreaker)

    with pytest.raises(LoopBreaker):
        main("dummy.yaml", status_file, False)

    mock_reset.assert_not_called()


def test_resume_while_still_on_battery_does_not_resnapshot(mocker, tmp_path):
    """
    If the host boots back up while the UPS is still on battery, the preserved
    'was online before the outage' flags must not be overwritten with the current
    (all offline) state.
    """
    status_file = str(tmp_path / "wolnut_state.json")
    _write_post_outage_state(status_file)

    mocker.patch(
        "wolnut.cli.load_config",
        return_value=_make_config(status_file, reset_state_on_resume=False),
    )
    mocker.patch(
        "wolnut.cli.get_ups_status",
        return_value={"ups.status": "OB DISCHRG", "battery.charge": "40"},
    )
    mocker.patch("wolnut.cli.is_client_online", return_value=False)
    mock_send_wol = mocker.patch("wolnut.cli.send_wol_packet", return_value=True)
    mock_snapshot = mocker.patch.object(ClientStateTracker, "mark_all_online_clients")
    mocker.patch("wolnut.cli.time.sleep", side_effect=LoopBreaker)

    with pytest.raises(LoopBreaker):
        main("dummy.yaml", status_file, False)

    mock_snapshot.assert_not_called()
    mock_send_wol.assert_not_called()

    # The persisted state still remembers the client was online before the outage.
    reloaded = ClientStateTracker([CLIENT], status_file=status_file)
    assert reloaded.was_online_before_shutdown(CLIENT.name)


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
