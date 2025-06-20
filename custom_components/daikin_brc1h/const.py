"""Constants for daikin_brc1h."""

import os
from datetime import timedelta
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "daikin_brc1h"

BLUETOOTH_DISCOVERY_TIMEOUT = 10.0
BLUETOOTH_DELAY = 0.2
MAX_TEMP = 32.0
MIN_TEMP = 16.0
TEMP_STEP = 1.0
DOMAIN_LOCK_KEY = "lock"

if os.environ.get("HA_DAIKIN_BRC1H_DEBUG", "0") == "0":
    COORDINATOR_UPDATE_INTERVAL = timedelta(seconds=60)
else:
    COORDINATOR_UPDATE_INTERVAL = timedelta(seconds=30)
