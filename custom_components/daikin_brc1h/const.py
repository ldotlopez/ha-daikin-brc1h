"""Constants for daikin_brc1h."""

from datetime import timedelta
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "daikin_brc1h"

BLUETOOTH_DISCOVERY_TIMEOUT = 10.0
MAX_TEMP = 32.0

MIN_TEMP = 16.0
TEMP_STEP = 1.0

COORDINATOR_UPDATE_INTERVAL = timedelta(seconds=60)
