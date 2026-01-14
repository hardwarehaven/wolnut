import click
import logging
import os
import time

from wolnut.config import load_config, DEFAULT_CONFIG_FILEPATHS
from wolnut.state import ClientStateTracker
from wolnut.monitor import get_ups_status, is_client_online
from wolnut.wol import send_wol_packet

logger = logging.getLogger("wolnut")


def configure_logger(level: str):
    """
    Configures the root logger's level.
    Needed for unit testing since logging.basicConfig is a no-op if the root logger already has handlers.
    """
    logger.setLevel(level)


def get_battery_percent(ups_status):
    return round(float(ups_status.get("battery.charge", 100)))


def main(config_file: str, status_file: str, verbose: bool = False) -> int:
    """MAIN LOOP"""
    config = load_config(config_file, status_path=status_file, verbose=verbose)
    if not config:
        return 1

    configure_logger(config.log_level)
    logger.info("WOLNUT started. Monitoring UPS: %s", config.nut.ups)

    on_battery = False
    recorded_down_clients = set()
    recorded_up_clients = set()
    battery_percent = 100
    restoration_event = False
    restoration_event_start = None
    wol_being_sent = False

    state_tracker = ClientStateTracker(config.clients, status_file=config.status_file)
    if state_tracker.was_ups_on_battery():
        logger.info("WOLNUT is resuming from a UPS battery event")
        restoration_event = True

    ups_status = get_ups_status(config.nut.ups)
    battery_percent = get_battery_percent(ups_status)
    power_status = ups_status.get("ups.status", "OL")
    logger.info("UPS power status: %s, Battery: %s%%", power_status, battery_percent)

    while True:
        ups_status = get_ups_status(config.nut.ups)
        battery_percent = get_battery_percent(ups_status)
        power_status = ups_status.get("ups.status", "OL")

        logger.debug(
            "UPS power status: %s, Battery: %s%%", power_status, battery_percent
        )

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
                    config.wake_on.min_battery_percent,
                )

            elif (
                time.time() - restoration_event_start < config.wake_on.restore_delay_sec
            ):
                logger.info(
                    "Power restored, waiting %s seconds before waking clients...",
                    int(
                        config.wake_on.restore_delay_sec
                        - (time.time() - restoration_event_start)
                    ),
                )

            else:
                if not wol_being_sent:
                    logger.info(
                        "Power restored and battery >= %s%%. Preparing to send WOL...",
                        config.wake_on.min_battery_percent,
                    )
                    wol_being_sent = True

                for client in config.clients:

                    if state_tracker.should_skip(client.name):
                        continue

                    if not state_tracker.was_online_before_shutdown(client.name):
                        logger.info(
                            "Skipping WOL for %s: was not online before power loss",
                            client.name,
                        )
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
                            client.name, config.wake_on.reattempt_delay
                        ):
                            logger.info(
                                "Sending WOL packet to %s at %s",
                                client.name,
                                client.mac,
                            )
                            if send_wol_packet(client.mac):
                                state_tracker.mark_wol_sent(client.name)
                        else:
                            logger.debug(
                                "Waiting to retry WOL for %s (delay not reached)",
                                client.name,
                            )

                if len(recorded_down_clients) == 0:
                    logger.info("Power Restored and all clients are back online!")
                    restoration_event = False
                    restoration_event_start = None
                    state_tracker.reset()
                    wol_being_sent = False
                else:
                    if (
                        time.time() - restoration_event_start
                        > config.wake_on.client_timeout_sec
                    ):
                        logger.warning(
                            "Some devices failed to come back online within the timeout period."
                        )
                        for client in recorded_down_clients:
                            logger.warning(
                                "%s failed to come back online within timeout period.",
                                client,
                            )
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

        state_tracker.save_state()

        if not on_battery:
            time.sleep(config.poll_interval)
        else:
            time.sleep(2)


@click.command()
@click.option(
    "--config-file",
    envvar="WOLNUT_CONFIG_FILE",
    help="The configuration filepath to load. Can also be set with WOLNUT_CONFIG_FILE env var.",
)
@click.option(
    "--status-file",
    envvar="WOLNUT_STATUS_FILE",
    help="The status filepath to load. Can also be set with WOLNUT_STATUS_FILE env var.",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def wolnut(config_file: str | None, status_file: str | None, verbose: bool) -> int:
    """A service to send Wake-on-LAN packets to clients after a power outage."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if verbose:
        configure_logger("DEBUG")

    if config_file is None:
        for path in DEFAULT_CONFIG_FILEPATHS:
            if os.path.exists(path):
                config_file = path
                break
        if config_file is None:
            click.echo(
                "No config file found. Checked default paths and WOLNUT_CONFIG_FILE env var."
            )
            raise click.Abort()

    exit_code = main(config_file, status_file, verbose)
    if exit_code != 0:
        # main() will log the specific error, so we just abort.
        raise click.Abort()
