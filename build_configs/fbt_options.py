# Sample FBT options configuration for custom firmware
# Copy this to your unleashed-firmware directory as fbt_options.py

import posixpath
from pathlib import Path

# Firmware origin identifier
FIRMWARE_ORIGIN = "NaTo1000-Custom"

# Default hardware target
TARGET_HW = 7

# Optimization flags
## Optimize for size
COMPACT = 0
## Optimize for debugging experience
DEBUG = 1

# Application to start on boot
# Set this to the exact name from your application.fam
LOADER_AUTOSTART = "Autostart Test"

# Optional: delay before launching the app on boot (seconds)
# LOADER_START_DELAY = 0.5

# Default radio stack
COPRO_STACK_BIN = "stm32wb5x_BLE_Stack_light_fw.bin"
COPRO_STACK_TYPE = "ble_light"

# Firmware application sets
FIRMWARE_APPS = {
    "default": [
        # Core services
        "basic_services",
        # Main applications
        "main_apps",
        "system_apps",
        # Settings
        "settings_apps",
    ],
    "minimal": [
        # Minimal set for testing
        "basic_services",
        "updater_app",
        "archive",
    ],
}

# Select which app set to build
FIRMWARE_APP_SET = "default"

# Custom local options
custom_options_fn = "fbt_options_local.py"

if Path(custom_options_fn).exists():
    exec(compile(Path(custom_options_fn).read_text(), custom_options_fn, "exec"))
