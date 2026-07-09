"""Sample FBT options configuration for custom firmware.

Copy this file to your unleashed-firmware build root as fbt_options.py.
It loads optional local overrides from fbt_options_local.py in the same directory.
"""

from pathlib import Path
from typing import Final, Optional, Union

# Firmware origin identifier
FIRMWARE_ORIGIN: Final[str] = "NaTo1000-Custom"

# Default hardware target
TARGET_HW: Final[int] = 7

# Optimization flags
## Optimize for size
COMPACT: Final[int] = 0
## Optimize for debugging experience
DEBUG: Final[int] = 1

# Application to start on boot.
# Must match the exact name from your application.fam.
# NOTE: "Autostart Test" is the bundled demo; change this for production builds.
LOADER_AUTOSTART: str = "Autostart Test"

# Optional: delay before launching the app on boot (seconds).
LOADER_START_DELAY: Optional[Union[float, int]] = None

# Default radio stack
COPRO_STACK_BIN: Final[str] = "stm32wb5x_BLE_Stack_light_fw.bin"
COPRO_STACK_TYPE: Final[str] = "ble_light"

# Known app-set name constants
APP_SET_DEFAULT: Final[str] = "default"
APP_SET_MINIMAL: Final[str] = "minimal"

# Firmware application sets
FIRMWARE_APPS: Final[dict] = {
    APP_SET_DEFAULT: [
        # Core services
        "basic_services",
        # Main applications
        "main_apps",
        "system_apps",
        # Settings
        "settings_apps",
    ],
    APP_SET_MINIMAL: [
        # Minimal set for testing
        "basic_services",
        "updater_app",
        "archive",
    ],
}

# Select which app set to build
FIRMWARE_APP_SET: str = APP_SET_DEFAULT


def _validate_app_set() -> None:
    """Raise ValueError if the selected app set is not defined in FIRMWARE_APPS."""
    if FIRMWARE_APP_SET not in FIRMWARE_APPS:
        valid = ", ".join(sorted(FIRMWARE_APPS))
        raise ValueError(
            f"Unknown FIRMWARE_APP_SET={FIRMWARE_APP_SET!r}. " f"Valid options: {valid}"
        )


_validate_app_set()

# ---------------------------------------------------------------------------
# Load optional local overrides from the Flipper build root.
# The local file is executed in an isolated namespace; only whitelisted
# variables are copied back so that helpers defined there cannot pollute
# this module.
# ---------------------------------------------------------------------------
_CUSTOM_OPTIONS_FILENAME: Final[str] = "fbt_options_local.py"
_local_options_path: Path = Path(__file__).with_name(_CUSTOM_OPTIONS_FILENAME)

if _local_options_path.is_file():
    # Provide __file__ so the local script can locate its own directory.
    _local_namespace: dict = {"__file__": str(_local_options_path)}
    _local_source: str = _local_options_path.read_text(encoding="utf-8")
    exec(  # noqa: S102
        compile(_local_source, str(_local_options_path), "exec"),
        _local_namespace,
    )

    # Only recognised keys are promoted back into this module's globals.
    _ALLOWED_OVERRIDES: Final[frozenset] = frozenset(
        {
            "FIRMWARE_ORIGIN",
            "TARGET_HW",
            "COMPACT",
            "DEBUG",
            "LOADER_AUTOSTART",
            "LOADER_START_DELAY",
            "COPRO_STACK_BIN",
            "COPRO_STACK_TYPE",
            "FIRMWARE_APPS",
            "FIRMWARE_APP_SET",
        }
    )

    for _key in _ALLOWED_OVERRIDES:
        if _key in _local_namespace:
            globals()[_key] = _local_namespace[_key]

    # Re-validate in case the local config changed the selected app set.
    _validate_app_set()
