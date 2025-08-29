import json
import os
from typing import Dict, Any
import logging
import time

logger = logging.getLogger("wolnut")
logger.setLevel(logging.INFO)


class ClientStateTracker:
    """
    Tracks the online/offline state of client systems and Wake-on-LAN activity
    during and after a UPS battery event.

    Attributes:
        _clients (list): List of clients being tracked.
        _state_file (str): Path to the JSON file for persisting state.
        _client_states (dict): Tracks per-client status info.
        _meta_state (dict): Tracks global UPS-related status.

    Methods:
        update(client_name, online): Updates online status.
        mark_wol_sent(client_name): Marks a client as having been sent a WOL packet.
        reset(): Clears all stored state information.
        ...
    """

    def __init__(self, clients, state_file: str = "wolnut_state.json"):
        self._clients = clients
        self._state_file = state_file
        self._meta_state: Dict[str, Any] = {
            "ups_on_battery": False,
            "battery_percent_at_shutdown": 100,
        }

        self._client_states: Dict[str, Dict[str, Any]] = {
            client.name: {
                "was_online_before_battery": False,
                "is_online": False,
                "wol_sent": False,
                "wol_sent_at": 0,
                "skip": False,
            }
            for client in clients
        }
        self._load_state()

    def _load_state(self):
        if not os.path.exists(self._state_file):
            return
        try:
            with open(self._state_file, "r") as f:
                save_data = json.load(f)

            self._meta_state.update(save_data["meta"])

            for name, state in save_data.get("clients", {}).items():
                if name in self._client_states:
                    self._client_states[name].update(state)

        except Exception as e:
            logger.warning("Failed to load state from file: %s", e)

    def _save_state(self):
        save_data = {"meta": self._meta_state, "clients": self._client_states}
        try:
            with open(self._state_file, "w") as f:
                json.dump(save_data, f)
        except Exception as e:
            logger.warning("Failed to save state to file: %s", e)

    def update(self, client_name: str, online: bool):
        if client_name in self._client_states:
            self._client_states[client_name]["is_online"] = online
        self._save_state()

    def mark_wol_sent(self, client_name: str):
        if client_name in self._client_states:
            self._client_states[client_name]["wol_sent"] = True
            self._client_states[client_name]["wol_sent_at"] = time.time()
        self._save_state()

    def mark_skip(self, client_name: str):
        if client_name in self._client_states:
            self._client_states[client_name]["skip"] = True
        self._save_state()

    def mark_all_online_clients(self):
        for name, state in self._client_states.items():
            state["was_online_before_battery"] = state["is_online"]
        self._save_state()

    def is_online(self, client_name: str) -> bool:
        return self._client_states.get(client_name, {}).get("is_online", False)

    def was_online_before_shutdown(self, client_name: str) -> bool:
        return self._client_states.get(client_name, {}).get(
            "was_online_before_battery", False
        )

    def has_been_wol_sent(self, client_name: str) -> bool:
        return self._client_states.get(client_name, {}).get("wol_sent", False)

    def should_attempt_wol(self, client_name: str, reattempt_delay: int) -> bool:
        state = self._client_states.get(client_name, {})
        last = state.get("wol_sent_at", 0)
        return time.time() - last >= reattempt_delay

    def should_skip(self, client_name: str) -> bool:
        return self._client_states.get(client_name, {}).get("skip", False)

    def set_ups_on_battery(self, is_on_battery: bool, battery_percent: int = 100):
        self._meta_state["ups_on_battery"] = is_on_battery
        self._meta_state["battery_percent_at_shutdown"] = battery_percent
        self._save_state()

    def was_ups_on_battery(self) -> bool:
        return self._meta_state["ups_on_battery"]

    def reset(self):
        for state in self._client_states.values():
            state["was_online_before_battery"] = False
            state["wol_sent"] = False
            state["skip"] = False
        self._save_state()
