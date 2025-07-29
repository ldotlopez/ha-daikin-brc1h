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

## Next steps

These are some next steps you may want to look into:

- Add tests to your integration, [`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) can help you get started.
- Add brand images (logo/icon) to https://github.com/home-assistant/brands.
- Create your first release.
- Share your integration on the [Home Assistant Forum](https://community.home-assistant.io/).
- Submit your integration to [HACS](https://hacs.xyz/docs/publish/start).
