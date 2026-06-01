#!/bin/bash
# USB/IP bridge — passes a physical Flipper Zero through to the VNC container
# Requires usbipd-win (Windows) or usbip-utils (Linux)

set -euo pipefail

FLIPPER_VENDOR_ID="0483"
FLIPPER_PRODUCT_ID="5740"

echo "[usbip-bridge] Looking for Flipper Zero (${FLIPPER_VENDOR_ID}:${FLIPPER_PRODUCT_ID})..."

# Find the bus ID of the connected Flipper
BUSID=$(usbip list -l 2>/dev/null | grep "${FLIPPER_VENDOR_ID}:${FLIPPER_PRODUCT_ID}" | awk '{print $1}' | tr -d ':')

if [ -z "$BUSID" ]; then
  echo "[usbip-bridge] ERROR: No Flipper Zero found. Connect the device and retry."
  exit 1
fi

echo "[usbip-bridge] Found Flipper at bus ID: ${BUSID}"
echo "[usbip-bridge] Binding device for USB/IP sharing..."
usbip bind --busid="${BUSID}"

echo "[usbip-bridge] Device bound. VNC container can now attach via:"
echo "  usbip attach -r <host-ip> -b ${BUSID}"
