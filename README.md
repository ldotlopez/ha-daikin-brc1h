# Daikin BRC1H Climate Integration for Home Assistant

### 🌬️ What is it?

This integration enables full<sup>(*)</sup> control and monitoring of Daikin AC units using the BRC1H series controller over Bluetooth.

It is a **local-only integration**, requiring no cloud or internet access.

<sup>(*)</sup> Core Home Assistant climate functions are supported. However, advanced Daikin features, such as master and secondary units, are not yet available.

###  ⚠️ Disclaimer

This is an early release; both the integration and the underlying library (kadoma) are still in the early stages of development. Errors and crashes should be expected.

The code has been tested under challenging conditions—multiple units on a single Bluetooth controller, unstable connections, long distances to the unit, etc. Although it includes automatic recovery and reconnection fallbacks, units may still disconnect occasionally.

### ✅ Features

* Configurable from UI
* View current temperature
* Change modes: Cool, Heat, Auto, Dry, Fan
* Adjust fan speed and swing settings (where supported)
* Turn units on/off
* Works with multiple units
* Auto-discovery and device info


### 🔧 Requirements

* Recent Home Assistant (~ 2024.06) installation.
* A bluetooth adapter.
* A working, **and paired**, to the Daikin BRC1H unit (some instructions below)

### 🧩 Installation

0. Before or after installation, manually pair the unit with your host.
1. Install the integration:
  * **Via HACS:** Add `daikin_brc1h` as a custom repository: `https://github.com/ldotlopez/ha-daikin-brc1h`
  * **Manually:** Copy the custom component into `custom_components/daikin_brc1h/`
2. Restart Home Assistant.
3. The unit(s) should be automatically detected and appear on the Integrations page. If not, manually add a **Daikin BRC1H Thermostat** integration for each AC unit.

Basic instructions to pair units:
```
# Set pairing mode on unit control panel

# Restart bluetooth service to avoid complications
$ sudo systemctl restart bluetooth

# Enter bluetootctl shell
$ bluetooth

# Once into bluetootctl
scan le
devices  # <-- This will show some devices
pair E4:A6:34:xx:xx:xx

# Confirm pair in the unit control panel
```
