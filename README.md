# About

Custom integration for Daikin BRC1H thermostats

## Pairing

This integration only works with already paired devices.

In order to pair a new thermostat you new to stop Home Assistant, run this instructions and start again Home Assistant

```shell
sudo systemctl restart bluetooth

scan le
devices
pair  E4:A6:34:xx:xx:xx
```

## Next steps

These are some next steps you may want to look into:
- Add tests to your integration, [`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) can help you get started.
- Add brand images (logo/icon) to https://github.com/home-assistant/brands.
- Create your first release.
- Share your integration on the [Home Assistant Forum](https://community.home-assistant.io/).
- Submit your integration to [HACS](https://hacs.xyz/docs/publish/start).
