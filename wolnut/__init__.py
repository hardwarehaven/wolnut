import logging
from wolnut.apprise_logging import apprise_notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("wolnut")

notifier = apprise_notifier("wolnut")