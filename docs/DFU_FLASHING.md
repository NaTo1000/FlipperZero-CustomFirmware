# DFU Flashing Guide

Complete instructions for flashing Flipper Zero firmware — both normal USB flashing
and low-level DFU (Device Firmware Upgrade) recovery.

---

## Method A — Normal USB Flash via FBT (recommended)

This is the standard workflow once the firmware builds successfully.

```bash
# Connect Flipper Zero via USB
cd unleashed-firmware

# Linux / macOS
./fbt flash_usb

# Windows
python fbt flash_usb
```

The FBT tool handles putting the device into programming mode automatically.

---

## Method B — DFU Recovery (device bricked / won't boot)

Use this when the Flipper Zero no longer boots and FBT can't detect it.

### Step 1 — Enter DFU mode

1. **Power off** the Flipper Zero (hold BACK for ~5 s).
2. **Hold the LEFT d-pad button** and keep holding it.
3. **Plug in the USB cable** while still holding LEFT.
4. The screen stays **dark** — this means DFU mode is active.

> **Tip**: On some hardware revisions, hold LEFT + BACK simultaneously while plugging in.

### Step 2 — Verify DFU is detected

```bash
dfu-util -l
```

Expected output includes:

```
Found DFU: [0483:df11] ver=2200, devnum=X, cfg=1, intf=0, path="X-X",
           alt=0, name="@Internal Flash  /0x08000000/..."
```

### Step 3 — Flash the firmware

```bash
# Replace with your actual dist path:
dfu-util \
  -d 0483:df11 \
  -a 0 \
  -s 0x08000000:leave \
  -D unleashed-firmware/dist/f7-D/flipper-z-full.dfu
```

The `-s 0x08000000:leave` flag tells the MCU to jump to the new firmware after flashing.

### Step 4 — Reboot

Disconnect USB. The Flipper should reboot into the new firmware automatically.
If it does not, hold BACK for 10 s to force a hard reset.

---

## Method C — qFlipper GUI (easiest for beginners)

1. Download and install **qFlipper**: <https://flipperzero.one/update>
2. Connect Flipper Zero via USB.
3. Click **"Install from file"**.
4. Browse to:
   ```
   unleashed-firmware/dist/f7-D/flipper-z-full.dfu
   ```
5. Click **Install** and wait for completion.
6. Flipper reboots automatically.

---

## Method D — Flash .fap Only (no full reflash)

If you only want to install **HackRF Companion** without reflashing the entire firmware:

```bash
cd unleashed-firmware

# Build the .fap
./fbt fap_hackrf_companion

# Deploy directly to connected Flipper via USB
./fbt launch_app APPSRC=applications_user/hackrf_companion
```

The `.fap` file is placed at:
```
unleashed-firmware/dist/f7-D/apps/Sub-GHz/hackrf_companion.fap
```

Copy it to the Flipper SD card under `apps/Sub-GHz/` using qFlipper or any file manager.

---

## Platform-Specific Notes

### Linux

Add a udev rule so you don't need `sudo`:

```bash
sudo bash -c 'cat > /etc/udev/rules.d/42-flipperzero.rules << EOF
# Flipper Zero — normal USB
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", TAG+="uaccess"
# Flipper Zero — DFU mode
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="df11", TAG+="uaccess"
EOF'

sudo udevadm control --reload-rules
sudo udevadm trigger
```

Install `dfu-util`:
```bash
sudo apt install dfu-util       # Debian / Ubuntu
sudo dnf install dfu-util       # Fedora
sudo pacman -S dfu-util         # Arch
```

### macOS

```bash
brew install dfu-util
```

No extra drivers required.

### Windows

1. Install **Zadig** from <https://zadig.akeo.ie/>.
2. Plug in Flipper Zero in DFU mode (hold LEFT + connect USB).
3. In Zadig, select **"STM32 BOOTLOADER"** from the device list.
4. Install the **WinUSB** or **libusb-win32** driver.
5. Install `dfu-util` from <https://dfu-util.sourceforge.net/>.

Or use the cross-platform installer which checks all of this:

```cmd
install.bat
```

---

## Troubleshooting DFU

| Problem | Solution |
|---------|----------|
| `dfu-util -l` shows nothing | Check USB cable; try a different port; verify DFU mode (screen dark) |
| "Cannot open DFU device" (Linux) | Add udev rule (see above) |
| "Cannot open DFU device" (Windows) | Install WinUSB driver via Zadig |
| Flash fails mid-way | Re-enter DFU mode and retry |
| Device still doesn't boot after flash | Hold BACK 10 s to hard-reset |
| Wrong `.dfu` file path | Check `dist/f7-D/` after running `./fbt` |

---

## Build Locations

After running `./fbt` inside `unleashed-firmware/`:

| File | Purpose |
|------|---------|
| `dist/f7-D/flipper-z-full.dfu` | Full firmware DFU image |
| `dist/f7-D/flipper-z-updater.bin` | OTA updater package |
| `dist/f7-D/apps/Sub-GHz/hackrf_companion.fap` | HackRF Companion .fap |

---

## Quick Reference

```
# Enter DFU mode:  Hold LEFT → plug USB → screen stays dark

# Verify DFU:      dfu-util -l  (expect [0483:df11])

# Flash:           dfu-util -d 0483:df11 -a 0 -s 0x08000000:leave \
#                            -D dist/f7-D/flipper-z-full.dfu

# .fap only:       ./fbt fap_hackrf_companion
#                  ./fbt launch_app APPSRC=applications_user/hackrf_companion

# DFU help:        python install.py --dfu
```
