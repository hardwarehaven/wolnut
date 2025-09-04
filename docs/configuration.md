# Configuration Guide

The `wolnut` service is configured using a single YAML file, typically named `config.yaml`. This guide details all the available configuration options.

## Top-Level Options

These options are at the root of the configuration file.

### `log_level`

Sets the verbosity of the application's logs.

-   **Type**: `string`
-   **Default**: `"INFO"`
-   **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### `poll_interval`

The interval in seconds at which `wolnut` checks the status of the UPS and clients during normal operation (when not on battery power). This should generally be shorter than the shutdown delay configured on your NUT clients.

-   **Type**: `integer`
-   **Default**: `15`

### `status_file`

The file path where `wolnut` will store its state. This allows the service to resume its logic after a restart. It's highly recommended to map this file to a persistent volume when using Docker.

-   **Type**: `string`
-   **Default**: `"/app/wolnut_state.json"`

---

## `nut`

Configuration for connecting to your NUT (Network UPS Tools) server.

-   `ups`: **(Required)** The name and address of the UPS to monitor.
    -   **Format**: `<ups-name>@<hostname-or-ip>`
-   `hostname`: The hostname of the NUT server. Defaults to `localhost`.
-   `port`: The port of the NUT server. Defaults to `3493`.
-   `username`: The username for authenticating with the NUT server (optional).
-   `password`: The password for authenticating with the NUT server (optional).

---

## `wake_on`

Parameters that control the Wake-on-LAN behavior after power is restored.

-   `restore_delay_sec`: The number of seconds to wait after AC power is restored before attempting to wake clients. This prevents sending WOL packets during brief power flickers.
    -   **Default**: `30`
-   `min_battery_percent`: `wolnut` will wait for the UPS battery to reach this percentage before sending WOL packets.
    -   **Default**: `25`
-   `client_timeout_sec`: The total time in seconds to wait for a client to come back online after a WOL packet has been sent. If the client doesn't appear online within this period, a warning is logged.
    -   **Default**: `600`
-   `reattempt_delay`: The minimum time in seconds between sending WOL packets to the same client if it doesn't come online.
    -   **Default**: `30`

---

## `clients`

A list of client machines to monitor and wake.

Each item in the list is an object with the following properties:

-   `name`: **(Required)** A human-readable name for the client. Used for logging.
-   `host`: **(Required)** The IP address or hostname of the client. This is used to check if the client is online via ping.
-   `mac`: **(Required)** The MAC address of the client's network interface.
    -   **Value**: Can be a standard MAC address string (e.g., `"DE:AD:BE:EF:00:01"`) or `"auto"`.
    -   If set to `"auto"`, `wolnut` will attempt to resolve the MAC address at startup using an ARP lookup based on the `host`.

### Example `clients` block:

```yaml
clients:
  - name: "desktop-pc"
    host: "192.168.1.100"
    mac: "38:f7:cd:c5:87:6b"

  - name: "media-server"
    host: "mediaserver.local"
    mac: "auto" # wolnut will find the MAC address for you
```