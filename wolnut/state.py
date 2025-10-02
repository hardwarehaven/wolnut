import json
import logging
import time

from hashlib import md5
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("wolnut")

DEFAULT_STATE_FILEPATH = "/config/wolnut_state.json"
ASSUME_UNINITIALIZED_ONLINE = False  # Assume clients are online if no state file exists


class ClientStateTracker:
    """
    Tracks the online/offline state of client systems and Wake-on-LAN activity
    during and after a UPS battery event.

    Attributes:
        _clients (list): List of clients being tracked.
        _status_file (str): Path to the JSON file for persisting state.
        _client_states (dict): Tracks per-client status info.
        _meta_state (dict): Tracks global UPS-related status.

    Methods:
        update(client_name, online): Updates online status.
        mark_wol_sent(client_name): Marks a client as having been sent a WOL packet.
        reset(): Clears all stored state information.
        ...
    """

    def __init__(self, clients: List[Any], status_file: str):
        # Search default locations for existing state file
        if not status_file:
            raise ValueError("A status file must be specified.")

        self._status_file = Path(status_file)  # Filename for storing state data
        self._status_hash = None  # Hash of the current/previous status file contents
        self._dirty = False  # Whether the state has changed since last save
        self._meta_state: Dict[str, Any] = {
            "ups_on_battery": False,
            "battery_percent_at_shutdown": 100,
        }
        self._client_states: Dict[str, Dict[str, Any]] = {}

        # Load existing state from file first
        if self._status_file.exists():
            self._load_state()

        # Initialize any clients not in the loaded state
        for client in clients:
            if client.name not in self._client_states:
                self._client_states[client.name] = {
                    "was_online_before_battery": ASSUME_UNINITIALIZED_ONLINE,
                    "is_online": False,
                    "wol_sent": False,
                    "wol_sent_at": 0,
                    "skip": False,
                }

    def _load_state(self):
        """
        Loads the state from the JSON file, if it exists.
        """
        try:
            with open(self._status_file, "r") as f:
                raw_data = f.read()

            # Remember the hash of the loaded data to avoid unnecessary writes later
            # I'm aware that md5 is not cryptographically secure, but this is not a security use case.
            status_hash = md5(raw_data.encode("utf-8")).hexdigest()
            save_data = json.loads(raw_data)
            self._meta_state.update(save_data["meta"])
            self._client_states = save_data.get("clients", {})
            self._status_hash = status_hash
            logger.info("State loaded from %s", self._status_file)
        except Exception as e:
            logger.warning("Failed to load state from file: %s", e)

    def save_state(self):
        """
        Saves the current state to the JSON file, if it has changed since the last save.
        The number of try/except blocks is intentional to ensure that errors are well
        documentented for debugging.
        """
        if not self._dirty:
            return

        save_data = {"meta": self._meta_state, "clients": self._client_states}
        try:
            # Make it pretty for humans
            raw_data = json.dumps(
                save_data, indent=4, separators=(",", ": "), sort_keys=True
            )
            new_hash = md5(raw_data.encode("utf-8")).hexdigest()
            if self._status_hash == new_hash:
                logging.debug("State unchanged, skipping save.")
                return
        except Exception:
            logger.exception("Failed to serialize state to JSON.")
            return

        temp_state_file = self._status_file.with_suffix(".json.tmp")
        try:
            with temp_state_file.open("w") as f:
                f.write(raw_data)
        except Exception:
            logger.exception(
                "Failed to write temporary state file: '%s'", temp_state_file
            )
            return

        try:
            temp_state_file.replace(self._status_file)
        except Exception:
            logger.exception(
                "Failed to move temporary state to permanent: '%s' to '%s'",
                temp_state_file,
                self._status_file,
            )

        self._status_hash = new_hash
        self._dirty = False
        logger.debug("State saved to %s", self._status_file)

    def update(self, client_name: str, online: bool):
        if (
            client_name in self._client_states
            and self._client_states[client_name]["is_online"] != online
        ):
            self._client_states[client_name]["is_online"] = online
            self._dirty = True

    def mark_wol_sent(self, client_name: str):
        if client_name in self._client_states:
            self._client_states[client_name]["wol_sent"] = True
            self._client_states[client_name]["wol_sent_at"] = int(time.time())
            self._dirty = True

    def mark_skip(self, client_name: str):
        if client_name in self._client_states and not self._client_states[
            client_name
        ].get("skip", False):
            self._client_states[client_name]["skip"] = True
            self._dirty = True

    def mark_all_online_clients(self):
        for name, state in self._client_states.items():
            state["was_online_before_battery"] = state["is_online"]
            self._dirty = True

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
        if self._meta_state["ups_on_battery"] != is_on_battery:
            self._meta_state["ups_on_battery"] = is_on_battery
            self._dirty = True

        if self._meta_state["battery_percent_at_shutdown"] != battery_percent:
            self._meta_state["battery_percent_at_shutdown"] = battery_percent
            self._dirty = True

    def was_ups_on_battery(self) -> bool:
        return self._meta_state["ups_on_battery"]

    def reset(self):
        for state in self._client_states.values():
            state.update(
                {
                    "was_online_before_battery": False,
                    "wol_sent": False,
                    "wol_sent_at": 0,
                    "skip": False,
                }
            )
        # Also reset the meta state for a complete reset
        self.set_ups_on_battery(False)
        self._dirty = True
