# ESPHome Bluetooth Proxy backend

The dashboard can receive Xiaomi Mi Scale advertisements through any ESPHome Bluetooth Proxy reachable over the network. It is not tied to an ESP32 board model.

Set these environment variables on the Docker container:

- `MISCALE_ESPHOME_HOST`: proxy hostname or IP (for example `192.168.88.52`). If omitted, the original local BlueZ scanner is used.
- `MISCALE_ESPHOME_API_KEY`: ESPHome Native API encryption key (`api.encryption.key`). Leave empty only if the proxy API does not use encryption.
- `MISCALE_SCALE_MAC`: Xiaomi scale BLE MAC address.
- `MISCALE_SCANNER`: leave enabled (`on` or omit); `off` disables both backends.

The remote backend uses `bleak-esphome` and ESPHome's Native API on port 6053. No local Bluetooth adapter or /run/dbus bind mount is required in proxy mode.

Keep secrets in Portainer environment variables, never in the public Git repository. A separate ESPHome proxy can replace the current one just by changing its address.

**Status:** The code is added but needs an end-to-end test with a live ESPHome proxy and scale before enabling automatic production container updates. Upstream sync conflicts will stop publication.
