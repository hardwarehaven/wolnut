import json

import pytest

from wolnut.cli import main
from wolnut.config import ClientConfig, NutConfig, WakeOnConfig, WolnutConfig


class _StopLoop(Exception):
    """Raised by the mocked time.sleep to break out of the infinite main() loop."""


@pytest.fixture
def config(tmp_path):
    status_file = tmp_path / "wolnut_state.json"
    return WolnutConfig(
        nut=NutConfig(ups="myups"),
        status_file=str(status_file),
        wake_on=WakeOnConfig(restore_delay_sec=0, min_battery_percent=20),
        clients=[ClientConfig(name="client-1", host="192.0.2.1", mac="AA:BB:CC:DD:EE:FF")],
    )


def _write_state_mid_outage(status_file):
    """
    Simulates the state file as it would be written right after the UPS went
    on battery, before the process crashed/restarted: client-1 was online
    when the outage began but has not yet received a WOL packet.
    """
    state = {
        "meta": {"ups_on_battery": True, "battery_percent_at_shutdown": 50},
        "clients": {
            "client-1": {
                "was_online_before_battery": True,
                "is_online": False,
                "wol_sent": False,
                "wol_sent_at": 0,
                "skip": False,
            }
        },
    }
    with open(status_file, "w") as f:
        json.dump(state, f)


def test_restart_during_outage_still_sends_wol(config, mocker):
    """
    Reproduces the restart-during-outage bug: the service crashes/restarts
    while the UPS is still on battery. By the time it comes back up, power
    has been restored, but the client is still down. WOLNUT must remember
    (from the persisted state file) that client-1 was online before the
    outage, and send it a WOL packet.
    """
    _write_state_mid_outage(config.status_file)

    mocker.patch("wolnut.cli.load_config", return_value=config)
    mocker.patch(
        "wolnut.cli.get_ups_status",
        return_value={"ups.status": "OL", "battery.charge": "100"},
    )
    mocker.patch("wolnut.cli.is_client_online", return_value=False)
    mock_send_wol = mocker.patch("wolnut.cli.send_wol_packet", return_value=True)
    mocker.patch("wolnut.cli.time.sleep", side_effect=_StopLoop)

    with pytest.raises(_StopLoop):
        main("unused-config.yaml", "unused-status.json")

    mock_send_wol.assert_called_once_with("AA:BB:CC:DD:EE:FF")
