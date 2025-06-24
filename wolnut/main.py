import time
import logging
from wolnut.config import load_config
from wolnut.state import ClientStateTracker
from wolnut.monitor import get_ups_status, is_client_online
from wolnut.wol import send_wol_packet
from wolnut.idrac import power_on_idrac_client


logger = logging.getLogger("wolnut")


def main():
    """MAIN LOOP"""
    config = load_config()

    logger.setLevel(config.log_level)
    logger.info("WOLNUT started. Monitoring UPS: %s", config.nut.ups)

    on_battery = False
    recorded_down_clients = set()
    recorded_up_clients = set()
    battery_percent = 100
    restoration_event = False
    restoration_event_start = None
    wol_being_sent = False

    state_tracker = ClientStateTracker(config.clients)
    if state_tracker.was_ups_on_battery():
        logger.info("WOLNUT is resuming from a UPS battery event")
        restoration_event = True
        state_tracker.reset()

    ups_status = get_ups_status(config.nut.ups)
    battery_percent = int(ups_status.get("battery.charge", 100))
    power_status = ups_status.get("ups.status", "OL")
    logger.info("UPS power status: %s, Battery: %s%%",
                power_status, battery_percent)

    while True:
        ups_status = get_ups_status(config.nut.ups)
        battery_percent = int(ups_status.get("battery.charge", 100))
        power_status = ups_status.get("ups.status", "OL")

        logger.debug("UPS power status: %s, Battery: %s%%",
                     power_status, battery_percent)

        # Check each client
        for client in config.clients:
            online = is_client_online(client.host)
            state_tracker.update(client.name, online)

        # Power Loss Event
        if "OB" in power_status and not on_battery:
            state_tracker.mark_all_online_clients()
            state_tracker.set_ups_on_battery(True, battery_percent)
            on_battery = True
            logger.warning("UPS switched to battery power.")

        # Power Restoration Event
        elif ("OL" in power_status and on_battery) or restoration_event:
            on_battery = False
            restoration_event = True

            if not restoration_event_start:
                restoration_event_start = time.time()

            if battery_percent < config.wake_on.min_battery_percent:
                logger.info(
                    """Power restored, but battery still below 
                    minimum percentage (%s%%/%s%%). Waiting...""",
                    battery_percent,
                    config.wake_on.min_battery_percent)

            elif time.time() - restoration_event_start < config.wake_on.restore_delay_sec:
                logger.info(
                    "Power restored, waiting %s seconds before waking clients...",
                    int(config.wake_on.restore_delay_sec-(time.time() - restoration_event_start)))

            else:
                if not wol_being_sent:
                    logger.info("Power restored and battery >= %s%%. Preparing to send WOL...",
                                config.wake_on.min_battery_percent)
                    wol_being_sent = True
                    
                                # Power on iDRAC clients
                # Power on iDRAC clients
                for idrac_client in config.idrac_clients:
                    power_on_idrac_client(
                        idrac_client.host,
                        idrac_client.username,
                        idrac_client.password,
                        idrac_client.verify_ssl
                    )


                for client in config.clients:

                    if state_tracker.should_skip(client.name):
                        continue

                    if not state_tracker.was_online_before_shutdown(client.name):
                        logger.info(
                            "Skipping WOL for %s: was not online before power loss", client.name)
                        state_tracker.mark_skip(client.name)
                        continue

                    if state_tracker.is_online(client.name):
                        if client.name not in recorded_up_clients:
                            logger.info("%s is online.", client.name)
                            recorded_down_clients.discard(client.name)
                            recorded_up_clients.update({client.name})
                        continue

                    else:
                        recorded_down_clients.update({client.name})
                        if state_tracker.should_attempt_wol(
                            client.name,
                            config.wake_on.reattempt_delay
                        ):
                            logger.info(
                                "Sending WOL packet to %s at %s", client.name, client.mac)
                            if send_wol_packet(client.mac):
                                state_tracker.mark_wol_sent(client.name)
                        else:
                            logger.debug(
                                "Waiting to retry WOL for %s (delay not reached)", client.name)

                if len(recorded_down_clients) == 0:
                    logger.info(
                        "Power Restored and all clients are back online!")
                    restoration_event = False
                    restoration_event_start = None
                    state_tracker.reset()
                    wol_being_sent = False
                else:
                    if time.time() - restoration_event_start > config.wake_on.client_timeout_sec:
                        logger.warning(
                            "Some devices failed to come back online within the timeout period.")
                        for client in recorded_down_clients:
                            logger.warning(
                                "%s failed to come back online within timeout period.", client)
                        restoration_event = False
                        restoration_event_start = None
                        wol_being_sent = False
                    else:
                        pass

        elif not on_battery and not restoration_event:
            state_tracker.reset()
            state_tracker.set_ups_on_battery(False)
            recorded_down_clients.clear()
            recorded_up_clients.clear()

        if not on_battery:
            time.sleep(config.poll_interval)
        else:
            time.sleep(2)


if __name__ == "__main__":
    main()
