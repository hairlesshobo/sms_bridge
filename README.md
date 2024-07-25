# About

`sms_bridge` is meant to be a simple API gateway that allows sending SMS messages directly to a USB-attached cellular modem.

## But... why?

I use a combination of both email and SMS messaging for network notifications. I reserve direct SMS notifications for urgent notifications (hard drive failure, WAN failure, etc) and the rest I send via email. Previously, I had Zabbix connected directly to the cellular modem, which worked, but it only allowed Zabbix to send SMS notifications. I wanted a way to send from multiple systems and decided a simple HTTP API would be the easiest way to achieve that.

## How it works

Its nothing fancy, a basic Python API created with FastAPI and uvicorn. There is currently no authentication so it definitely shouldn't be used in any sort of production environment, but in my home lab, it works fine.

Ideally this should be hosted behind a reverse proxy with HTTPS termination, and external authentication of some sort, but I haven't needed to do that for my simple use case.

## Requirements

- Linux host (macOS or Windows might work - never tried)
- Docker + Docker Compose (technically optional, but the example below uses docker compose)
- Cellular modem connected to host with active mobile subscription

IMPORTANT NOTE: The cellular modem must be in the correct "mode". Many of these devices start in a mass storage mode upon first connection to the system, and it is up to the software to trigger the mode change into "modem" mode. Personally, this annoys me to no end because I am still struggling to create a udev rule that actually works to trigger this ever time the system boots, but for now I have my system configured to run the mode switch on boot.

For reference, this is the command I run for my own cellular modem in order to put it into the proper mode. Unless you run the same exact modem I do, this comment will 99% NOT be the one that you need to run, but I am putting it here for reference.

```bash
usb_modeswitch -v 12d1 -p 1f01 -X
```

## How to use it

### Docker Compose example

The below example requires that the modem be located at `/dev/serial/by-id/usb-HUAWEI_MOBILE_HUAWEI_MOBILE-if00-port0`, you will most likely need to change this to the path of your modem TTY. I **highly** recommend mapping the device by id (eg: `/dev/serial/by-id/....`) because, in my experience, the `/dev/ttyUSBxx` path can change between reboots.

- Create a directory to hold the tool, name it whatever you want - I use `./sms_bridge/`
```bash
mkdir sms_bridge
cd sms_bridge
```
- Clone this repo to a subdirectory called `source`
```bash
git clone https://github.com/hairlesshobo/sms_bridge.git source
```
- Create the `docker-compose.yml` file as follows (edit as necessary):
```yaml
version: '3.5'

services:
  sms_bridge:
    build:
      context: ./source/
    restart: unless-stopped
    ports:
     - "1780:80"
    devices:
      - "/dev/serial/by-id/usb-HUAWEI_MOBILE_HUAWEI_MOBILE-if00-port0:/dev/ttyUSB0"
    environment:
      - SERIAL_PORT=/dev/ttyUSB0 
      - LISTEN_PORT=80
```
- Start the app
```bash
docker-compose up -d --build
```

## API
The API for this is insanely simple. There is only one endpoint, `/send_sms/` and it accepts a body containing the recipient and message. The recipient (phone number) must include the preceeding `+` and the country code, for example for the United States: `+18005551234`

Quick example using `curl`:

```bash
curl --request POST \
  --url http://localhost:1780/send_sms/ \
  --header 'Content-Type: application/json' \
  --data '{
	"recipient": "+1235559876",
	"message": "This is a test sent from the SMS bridge"
    }'
```

# LICENSE

This utility is licensed under the MIT license, see the LICENSE file for more details

