# About

Custom integration for Daikin BRC1H thermostats

## Pairing

This integration only works with already paired devices.

In order to pair a new thermostat, run this instructions:

It's possible that you need to stop Home Assistant to pair the device.

```shell
# Restart bluetooth service to avoid complications
$ sudo systemctl restart bluetooth

# Enter bluetootctl shell
$ bluetooth

# Once into bluetootctl
scan le
devices  # <-- This will show some devices
pair E4:A6:34:xx:xx:xx
```
