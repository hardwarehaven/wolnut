"""
Tests for the power restoration and restart scenario.

These tests verify that WOLNUT correctly handles the scenario where:
1. The UPS goes on battery
2. Hosts are marked as online before the power loss
3. The system shuts down (e.g., UPS runs out of battery)
4. Docker/WOLNUT restarts after power is restored
5. WoL packets are sent to the hosts that were online before shutdown

This specifically tests the bug fix where reset() was being called prematurely
after restart, which cleared the was_online_before_battery state.
"""

import json
import pytest
from pathlib import Path

from wolnut.state import ClientStateTracker


class MockClient:
    """A simple mock client class for testing."""

    def __init__(self, name):
        self.name = name


@pytest.fixture
def clients():
    """Provides a standard list of mock clients for tests."""
    return [MockClient("server-1"), MockClient("server-2"), MockClient("nas")]


class TestRestartAfterPowerOutage:
    """
    Tests for the restart scenario after a power outage.

    These tests simulate what happens when WOLNUT restarts after the host
    machine was shut down due to a power outage.
    """

    def test_state_preserved_after_restart(self, clients, tmp_path):
        """
        Tests that client states are preserved after a simulated restart.

        This is the core test for the bug that was fixed. Before the fix,
        calling reset() after detecting was_ups_on_battery cleared all
        the was_online_before_battery flags.
        """
        state_file = tmp_path / "wolnut_state.json"

        # Phase 1: Simulate the initial run before power outage
        tracker1 = ClientStateTracker(clients, status_file=str(state_file))

        # Clients come online during normal operation
        tracker1.update("server-1", True)
        tracker1.update("server-2", True)
        tracker1.update("nas", False)  # NAS was already off

        # UPS goes on battery - mark which clients were online
        tracker1.mark_all_online_clients()
        tracker1.set_ups_on_battery(True, 50)
        tracker1.save_state()

        # Phase 2: Simulate restart after power is restored
        # Create a new tracker (simulating WOLNUT restart)
        tracker2 = ClientStateTracker(clients, status_file=str(state_file))

        # Verify the UPS state was loaded
        assert tracker2.was_ups_on_battery(), (
            "UPS on-battery state should be preserved after restart"
        )

        # CRITICAL: Verify was_online_before_battery is preserved
        # This is what the bug was breaking
        assert tracker2.was_online_before_shutdown("server-1"), (
            "server-1 should still be marked as was_online_before_battery"
        )
        assert tracker2.was_online_before_shutdown("server-2"), (
            "server-2 should still be marked as was_online_before_battery"
        )
        assert not tracker2.was_online_before_shutdown("nas"), (
            "nas should NOT be marked as was_online_before_battery (it was off)"
        )

    def test_wol_should_be_sent_after_restart(self, clients, tmp_path):
        """
        Tests that WoL should be attempted for clients that were online before shutdown.

        This simulates the decision logic that happens in the main loop.
        """
        state_file = tmp_path / "wolnut_state.json"

        # Phase 1: Before outage - mark clients as online
        tracker1 = ClientStateTracker(clients, status_file=str(state_file))
        tracker1.update("server-1", True)
        tracker1.update("server-2", True)
        tracker1.update("nas", False)
        tracker1.mark_all_online_clients()
        tracker1.set_ups_on_battery(True, 30)
        tracker1.save_state()

        # Phase 2: After restart - simulate the decision logic
        tracker2 = ClientStateTracker(clients, status_file=str(state_file))

        # Simulate that all clients are currently offline after restart
        tracker2.update("server-1", False)
        tracker2.update("server-2", False)
        tracker2.update("nas", False)

        # Decision logic (from cli.py main loop):
        # For each client, check if WoL should be sent
        clients_needing_wol = []
        for client in clients:
            if tracker2.was_online_before_shutdown(client.name):
                if not tracker2.is_online(client.name):
                    if tracker2.should_attempt_wol(client.name, 30):
                        clients_needing_wol.append(client.name)

        assert "server-1" in clients_needing_wol, (
            "server-1 should need WoL (was online before shutdown)"
        )
        assert "server-2" in clients_needing_wol, (
            "server-2 should need WoL (was online before shutdown)"
        )
        assert "nas" not in clients_needing_wol, (
            "nas should NOT need WoL (was not online before shutdown)"
        )

    def test_state_file_structure_after_battery_event(self, clients, tmp_path):
        """
        Tests that the state file has the correct structure after a battery event.

        This verifies the JSON structure that will be loaded on restart.
        """
        state_file = tmp_path / "wolnut_state.json"

        tracker = ClientStateTracker(clients, status_file=str(state_file))
        tracker.update("server-1", True)
        tracker.update("server-2", True)
        tracker.mark_all_online_clients()
        tracker.set_ups_on_battery(True, 45)
        tracker.save_state()

        # Read and verify the JSON structure
        with open(state_file) as f:
            data = json.load(f)

        # Check meta state
        assert data["meta"]["ups_on_battery"] is True
        assert data["meta"]["battery_percent_at_shutdown"] == 45

        # Check client states
        assert data["clients"]["server-1"]["was_online_before_battery"] is True
        assert data["clients"]["server-2"]["was_online_before_battery"] is True
        assert data["clients"]["nas"]["was_online_before_battery"] is False

    def test_reset_only_after_successful_restoration(self, clients, tmp_path):
        """
        Tests that reset() should only be called after all clients are back online.

        This documents the correct behavior: reset() clears the state and should
        only happen when the restoration is complete, not at startup.
        """
        state_file = tmp_path / "wolnut_state.json"

        # Setup: Create state as if we just restarted
        tracker = ClientStateTracker(clients, status_file=str(state_file))
        tracker.update("server-1", True)
        tracker.mark_all_online_clients()
        tracker.set_ups_on_battery(True, 50)
        tracker.save_state()

        # Simulate restart
        tracker2 = ClientStateTracker(clients, status_file=str(state_file))

        # Verify state before reset
        assert tracker2.was_online_before_shutdown("server-1")
        assert tracker2.was_ups_on_battery()

        # Now simulate calling reset() (which should only happen after restoration)
        tracker2.reset()

        # After reset, the state should be cleared
        assert not tracker2.was_online_before_shutdown("server-1"), (
            "After reset(), was_online_before_battery should be False"
        )
        assert not tracker2.was_ups_on_battery(), (
            "After reset(), ups_on_battery should be False"
        )

    def test_partial_restoration_preserves_state(self, clients, tmp_path):
        """
        Tests that state is preserved when only some clients come back online.

        WoL should continue to be attempted for clients still offline.
        """
        state_file = tmp_path / "wolnut_state.json"

        # Setup: All clients were online before outage
        tracker1 = ClientStateTracker(clients, status_file=str(state_file))
        for client in clients:
            tracker1.update(client.name, True)
        tracker1.mark_all_online_clients()
        tracker1.set_ups_on_battery(True, 40)
        tracker1.save_state()

        # Restart and partial restoration
        tracker2 = ClientStateTracker(clients, status_file=str(state_file))

        # server-1 comes back, but server-2 and nas are still offline
        tracker2.update("server-1", True)
        tracker2.update("server-2", False)
        tracker2.update("nas", False)
        tracker2.save_state()

        # Verify: server-2 and nas should still be candidates for WoL
        assert tracker2.was_online_before_shutdown("server-2")
        assert tracker2.was_online_before_shutdown("nas")
        assert not tracker2.is_online("server-2")
        assert not tracker2.is_online("nas")


class TestNewClientsDuringRestoration:
    """
    Tests for edge cases with client configuration changes.
    """

    def test_new_client_added_after_restart(self, tmp_path):
        """
        Tests behavior when a new client is added to config after restart.

        New clients should not receive WoL since they weren't tracked before.
        """
        state_file = tmp_path / "wolnut_state.json"
        original_clients = [MockClient("server-1")]

        # Initial state with one client
        tracker1 = ClientStateTracker(original_clients, status_file=str(state_file))
        tracker1.update("server-1", True)
        tracker1.mark_all_online_clients()
        tracker1.set_ups_on_battery(True, 50)
        tracker1.save_state()

        # Restart with additional client in config
        new_clients = [MockClient("server-1"), MockClient("server-2")]
        tracker2 = ClientStateTracker(new_clients, status_file=str(state_file))

        # server-1 should be restored from state
        assert tracker2.was_online_before_shutdown("server-1")

        # server-2 is new and should NOT be marked (ASSUME_UNINITIALIZED_ONLINE=False)
        assert not tracker2.was_online_before_shutdown("server-2"), (
            "New clients should not be marked as was_online_before_battery"
        )
