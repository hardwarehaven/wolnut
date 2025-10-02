# Quickstart Guide

This guide will help you get `wolnut` running in a few simple steps using Docker.

## Prerequisites

- Docker installed and running.
- A NUT (Network UPS Tools) server monitoring your UPS. See [Techno Tim's](https://technotim.live/posts/NUT-server-guide/) guide
- The IP address or hostname of your NUT server, probably localhost.
- The name of the UPS as configured in NUT (e.g., `ups`).

## Step 1: Create Configuration Directory and File

`wolnut` needs a configuration file to run. It's best to store this outside the container.

1.  Create a directory to hold your configuration:
    ```bash
    mkdir ~/wolnut
    ```

2.  Create an empty configuration file inside that directory:
    ```bash
    touch ~/wolnut/config.yaml
    ```

## Step 2: Configure `config.yaml`

Open `~/wolnut/config.yaml` in your favorite text editor and add the following minimal configuration. Be sure to replace the placeholder values with your actual details.

```yaml
# ~/wolnut/config.yaml

nut:
  # The name of your UPS as defined in your NUT server configuration.
  # Format: <ups-name>
  ups: "ups"
  hostname: "127.0.0.1"  # not needed if running localhost/127.0.0.1

# The directory for the status file should be writable. It will be created if it doesn't exist.
status_file: "/config/wolnut_state.json" 

clients:
  - name: "my-pc"
    host: "192.168.1.100" # IP address or hostname of the client machine
    mac: "DE:AD:BE:EF:00:01" # MAC address of the client machine
```

For more advanced options, see the [Configuration](configuration.md) Guide.

## Step 3: Run the Docker Container

Run the following command to start the `wolnut` container. The `--network host` flag is required for Wake-on-LAN and for `wolnut` to communicate with your NUT server on the local network.

```bash
docker run -d \
  --name wolnut \
  --restart unless-stopped \
  --network host \
  -v ~/wolnut:/config \
  hardwarehaven/wolnut:latest
```

### Docker Compose

See [docker-compose.yml](docker-compose.yml) for an example docker compose file

## Step 4: Check the Logs

You can check the logs to ensure `wolnut` started correctly and is monitoring your UPS.

```bash
docker logs wolnut
```

You should see output indicating that `wolnut` has started and successfully connected to your NUT server.

That's it! `wolnut` is now running and will automatically wake your configured clients after a power outage.