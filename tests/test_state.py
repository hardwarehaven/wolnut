import os
import pytest
import time

from pathlib import Path
from wolnut import state


# A simple mock client class for testing, as ClientStateTracker expects objects
# with a `.name` attribute.
class MockClient:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def clients():
    """Provides a standard list of mock clients for tests."""
    return [MockClient("client-1"), MockClient("client-2")]


@pytest.fixture
def tracker(clients, tmp_path):
    """Provides a ClientStateTracker instance using a temporary state file."""
    state_file = tmp_path / "wolnut_state.json"  # tmp_path is a pytest fixture
    return state.ClientStateTracker(clients, status_file=str(state_file))


def test_initial_state(tracker):
    """Tests that a new tracker initializes with correct default values."""
    assert not tracker.was_ups_on_battery()
    assert not tracker.is_online("client-1")
    assert not tracker.was_online_before_shutdown("client-1")
    assert not tracker.has_been_wol_sent("client-1")
    assert not tracker.should_skip("client-1")
    assert tracker.should_attempt_wol("client-1", 30)


def test_init_requires_status_file(clients):
    """Tests that ClientStateTracker raises ValueError if no status_file is provided."""
    with pytest.raises(ValueError, match="A status file must be specified."):
        # Pass None for status_file
        state.ClientStateTracker(clients, status_file=None)


def test_save_and_load_state(clients, tmp_path):
    """Tests that state can be saved to a file and loaded back correctly."""
    state_file = tmp_path / "wolnut_state.json"

    # 1. Create a tracker, modify its state, which triggers saves.
    tracker1 = state.ClientStateTracker(clients, status_file=str(state_file))
    tracker1.update("client-1", True)
    tracker1.mark_all_online_clients()
    tracker1.mark_wol_sent("client-2")
    tracker1.set_ups_on_battery(True, 50)
    tracker1.save_state()  # Explicitly save the state to the file

    # 2. Create a new tracker instance from the same file.
    tracker2 = state.ClientStateTracker(clients, status_file=str(state_file))

    # 3. Assert that the state was loaded correctly.
    assert tracker2.was_ups_on_battery()
    assert tracker2._meta_state["battery_percent_at_shutdown"] == 50
    # is_online is transient and not expected to be loaded.
    assert tracker2.was_online_before_shutdown("client-1")
    assert not tracker2.was_online_before_shutdown("client-2")
    assert tracker2.has_been_wol_sent("client-2")


def test_load_state_corrupted_file(clients, tmp_path, caplog):
    """Tests that a warning is logged when the state file is corrupted."""
    state_file = tmp_path / "corrupted_state.json"
    state_file.write_text("this is not valid json")

    tracker = state.ClientStateTracker(clients, status_file=str(state_file))
    assert (
        "Failed to load state from file" in caplog.text
    ), "A warning should be logged for a corrupted state file."
    assert (
        not tracker.was_ups_on_battery()
    ), "State should be default after a failed load."


def test_load_state_file_not_found(clients, tmp_path):
    """Tests that a new state file is created if one doesn't exist, without logging an error."""
    state_file = tmp_path / "new_state.json"
    assert not state_file.exists()
    state.ClientStateTracker(clients, status_file=str(state_file))
    # No error should be raised, and the tracker should initialize cleanly.


def test_update_and_is_online(tracker):
    """Tests the update and is_online methods."""
    assert not tracker.is_online("client-1")
    tracker.update("client-1", True)
    assert tracker.is_online("client-1")
    tracker.update("client-1", False)
    assert not tracker.is_online("client-1")


def test_mark_all_online_clients(tracker):
    """Tests marking all currently online clients for future WOL."""
    tracker.update("client-1", True)
    tracker.update("client-2", False)

    tracker.mark_all_online_clients()

    assert tracker.was_online_before_shutdown("client-1")
    assert not tracker.was_online_before_shutdown("client-2")


def test_should_attempt_wol(tracker, mocker):
    """Tests the logic for WOL re-attempt delays based on time."""
    reattempt_delay = 30
    # Initially, we should always be able to attempt.
    assert tracker.should_attempt_wol("client-1", reattempt_delay)

    # Mark WOL as sent.
    mock_time = mocker.patch("wolnut.state.time.time")
    mock_time.return_value = 1000.0
    tracker.mark_wol_sent("client-1")

    # Immediately after, we should not attempt.
    assert not tracker.should_attempt_wol("client-1", reattempt_delay)

    # After some time, but less than the delay, we should not attempt.
    mock_time.return_value = 1000.0 + reattempt_delay - 5
    assert not tracker.should_attempt_wol("client-1", reattempt_delay)

    # After the delay has passed, we should attempt.
    mock_time.return_value = 1000.0 + reattempt_delay
    assert tracker.should_attempt_wol("client-1", reattempt_delay)


def test_reset(tracker):
    """Tests that the reset method clears the correct state fields."""
    # Set some state to non-default values
    tracker.set_ups_on_battery(True, 50)
    tracker.update("client-1", True)
    tracker.mark_wol_sent("client-1")
    tracker.mark_skip("client-2")

    # Sanity check
    assert tracker.was_ups_on_battery()
    assert tracker.has_been_wol_sent("client-1")
    assert tracker.should_skip("client-2")

    tracker.reset()

    # Assert that resettable fields are cleared
    assert not tracker.was_ups_on_battery()
    assert not tracker.has_been_wol_sent("client-1")
    assert not tracker.should_skip("client-2")
    # is_online is not part of the reset logic, it reflects current state.
    assert tracker.is_online("client-1")


def test_mark_and_should_skip(tracker):
    """Tests the mark_skip and should_skip methods."""
    assert not tracker.should_skip("client-1")
    tracker.mark_skip("client-1")
    assert tracker.should_skip("client-1")


def test_set_and_was_ups_on_battery(tracker):
    """Tests the set_ups_on_battery and was_ups_on_battery methods."""
    assert not tracker.was_ups_on_battery()
    tracker.set_ups_on_battery(True, 75)
    assert tracker.was_ups_on_battery()
    assert tracker._meta_state["battery_percent_at_shutdown"] == 75

    tracker.set_ups_on_battery(False, 100)
    assert not tracker.was_ups_on_battery()
    assert tracker._meta_state["battery_percent_at_shutdown"] == 100


def test_state_not_saved_if_unchanged(tracker, mocker):
    """Tests that _save_state is skipped if the state hash hasn't changed."""
    # Initial save on update
    mock_open = mocker.spy(Path, "open")
    tracker.update("client-1", True)
    tracker.save_state()
    assert mock_open.call_count == 1

    # Another update with the same value should not trigger a save
    tracker.update("client-1", True)
    tracker.save_state()
    # The call count should still be 1 because the state data has not changed
    assert mock_open.call_count == 1

    # A different value should trigger a save
    tracker.update("client-1", False)
    tracker.save_state()
    assert mock_open.call_count == 2


def test_atomic_save_mechanism(tracker, tmp_path, mocker):
    """Tests that a temporary file is used for saving state."""
    state_file = tmp_path / "wolnut_state.json"
    temp_file = state_file.with_suffix(".json.tmp")
    tracker._status_file = state_file

    # Mock Path.open to intercept the file write
    mock_open = mocker.patch("pathlib.Path.open", mocker.mock_open())

    # Trigger a save
    tracker.update("client-1", True)  # Make state dirty
    tracker.save_state()

    # Assert that `open` was called on the temp_file Path object.
    mock_open.assert_called_once_with("w")


def test_methods_handle_unknown_client(tracker):
    """Tests that methods gracefully handle a client name not in the state."""
    unknown = "unknown-client"
    assert not tracker.is_online(unknown)
    assert not tracker.was_online_before_shutdown(unknown)
    assert not tracker.has_been_wol_sent(unknown)
    assert not tracker.should_skip(unknown)
    # should_attempt_wol should be true for a new client
    assert tracker.should_attempt_wol(unknown, 30)


def test_save_state_json_serialization_error(tracker, mocker, caplog):
    """Tests that an error is logged if JSON serialization fails during save."""
    mocker.patch("wolnut.state.json.dumps", side_effect=TypeError("Test error"))
    tracker.update("client-1", True)  # Make the state dirty
    tracker.save_state()
    assert "Failed to serialize state to JSON" in caplog.text


def test_save_state_temp_file_write_error(tracker, mocker, caplog):
    """Tests that an error is logged if writing the temporary state file fails."""
    mock_open = mocker.patch(
        "pathlib.Path.open", side_effect=IOError("Permission denied")
    )
    tracker.update("client-1", True)  # Make the state dirty
    tracker.save_state()
    assert "Failed to write temporary state file" in caplog.text


def test_save_state_rename_error(tracker, mocker, caplog):
    """Tests that an error is logged if renaming the temp file fails."""
    # We only want to mock the 'replace' method
    mocker.patch("pathlib.Path.replace", side_effect=OSError("Test rename error"))
    tracker.update("client-1", True)  # Make the state dirty
    tracker.save_state()
    assert "Failed to move temporary state to permanent" in caplog.text
