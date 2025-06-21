import apprise
import logging

logger = logging.getLogger("wolnut")
apprise_instance = {}

class apprise_notifier:
    def __init__(self, name: str = "apprise") -> None:
        """ Initializes the Apprise notifier using the provided name or retrieves an existing instance.

        Args:
            name (str, optional): Name of the Apprise instance. Defaults to "apprise".
        """
        if name in apprise_instance:
            self._apprise_instance = apprise_instance[name]
            return
        self._apprise_instance = apprise.Apprise()
        apprise_instance[name] = self._apprise_instance
        
    def _apprise_notify( self, body: str, notify_level: int, title: str) -> None:
        """
        Sends a notification using the Apprise instance.

        Args:
            body (str): Body of the notification.
            notify_type (int): Notification Level.
            title (str): Title of the notification.
        """
        if not self._apprise_instance:
            logging.debug("Apprise instance is not initialized. Cannot send notification.")
            return
        
        if notify_level < logger.getEffectiveLevel():
            return
        
        match notify_level:
            case logging.DEBUG:
                notify_type = apprise.NotifyType.INFO
            case logging.INFO:
                notify_type = apprise.NotifyType.INFO
            case logging.WARNING:
                notify_type = apprise.NotifyType.WARNING
            case logging.ERROR:
                notify_type = apprise.NotifyType.FAILURE
            case _:
                notify_type = apprise.NotifyType.INFO
        
        try:
            response = self._apprise_instance.notify(
                body=body,
                notify_type=notify_type,
                title=title,
            )
            if response:
                logging.info("Notification sent successfully: %s", title)
            else:
                logging.error("Failed to send notification: %s", title)
        except Exception as e:
            logging.error("Error sending notification: %s", e)

    def debug(self, body: str,  title: str = "WOLNUT Debug") -> None:
        """
        Sends a debug notification.
        Args:
            body (str): Body of the notification.
            title (str, optional): Title of the notification. Defaults to "WOLNUT Debug".
        """
        logger.debug(body)
        self._apprise_notify(body, logging.DEBUG, title)

    def info(self, body: str,   title: str = f"WOLNUT Notification") -> None:
        """
        Sends an informational notification.

        Args:
            body (str): Body of the notification.
            title (str, optional): Title of the notification. Defaults to "WOLNUT Notification".
        """
        logger.info(body)
        self._apprise_notify(body, logging.INFO, title)
        
    def warning(self, body: str, title: str = "WOLNUT Warning") -> None:
        """
        Sends a warning notification.
        Args:
            body (str): Body of the notification.
            title (str, optional): Title of the notification. Defaults to "WOLNUT Warning".
        """
        logger.warning(body)
        self._apprise_notify(body, logging.WARNING, title)
        
    def error(self, body: str, title: str = "WOLNUT Error") -> None:
        """
        Sends an error notification.
        Args:
            body (str): Body of the notification.
            title (str, optional): Title of the notification. Defaults to "WOLNUT Error".
        """
        logger.error(body)
        self._apprise_notify(body, logging.ERROR, title)
        
    def addUrls(self, urls: list[str]) -> None:
        """
        Adds notification URLs to the Apprise instance.

        Args:
            urls (list[str]): List of Apprise URLs to add.
        """
        if not urls:
            logging.debug("No Apprise URLs provided. Skipping addition.")
            return
        self._apprise_instance.add(urls)
        
    def setLevel(self, level: int | str) -> None:
        """
        Sets the logging level for the Apprise notifier.

        Args:
            level (int): Logging level to set.
        """
        logger.setLevel(level)