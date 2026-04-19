# HackRF Companion

SDR-inspired RF control panel for Flipper Zero, built on the CC1101 Sub-GHz radio.

Inspired by the [HackRF One](https://greatscottgadgets.com/hackrf/) tool suite
(`hackrf-2026.01.3` – NetBSD pkgsrc/ham/hackrf).

---

## Features

| View | Description |
|------|-------------|
| **Dashboard** | Live frequency display, real-time RSSI bar, modulation info, signal detection alert |
| **Scanner** | Spectrum sweep across the selected frequency band (28-column bar chart) |
| **Monitor** | Scrolling RSSI history graph with min/max/current stats |
| **Settings** | Adjust frequency preset, modulation type, and scan band |

### Live Metrics
- **RSSI** – Received Signal Strength Indicator (dBm) sampled every 100 ms
- **Peak RSSI** – Highest recorded signal level since last reset
- **Signal Detection** – LED blink + screen alert when RSSI > −80 dBm
- **Band Sweep** – 28-point spectrum scan across any of four common ISM bands

---

## Controls

| Button | Action |
|--------|--------|
| **←** / **→** | Switch between the four views |
| **↑** / **↓** | Tune frequency (Dashboard) / Change band (Scanner) / Navigate settings |
| **OK** | Toggle RX radio (Dashboard) / Start-Stop scan (Scanner) / Clear graph (Monitor) / Apply settings |
| **BACK** | Exit application |

---

## Frequency Presets

| Preset | Frequency | Notes |
|--------|-----------|-------|
| 315.000 MHz | 315 MHz | NA garage doors, remotes |
| **433.920 MHz** | 433.92 MHz | **Default** – EU/AU ISM, key fobs |
| 868.350 MHz | 868.35 MHz | EU SRD, LoRa, Z-Wave |
| 915.000 MHz | 915 MHz | US ISM, LoRa |

---

## Modulations

| Mode | HackRF Equivalent | Use Case |
|------|------------------|----------|
| **OOK** | AM/OOK | Garage doors, remote controls |
| **FSK2** | 2-FSK | LoRa, wireless sensors |
| **GFSK** | GFSK | Bluetooth-like, iBeacon |

---

## Installation

### As a .fap (External Application — no firmware reflash needed)

```bash
# Inside unleashed-firmware directory:
cp -r ../FlipperZero-CustomFirmware/applications_user/hackrf_companion applications_user/
./fbt fap_hackrf_companion

# Copy the built .fap to your Flipper's SD card:
./fbt launch_app APPSRC=applications_user/hackrf_companion
```

### Embedded into Firmware

```bash
cp -r ../FlipperZero-CustomFirmware/applications_user/hackrf_companion \
      ../unleashed-firmware/applications_user/
cd ../unleashed-firmware
./fbt
./fbt flash_usb
```

See [../../docs/DFU_FLASHING.md](../../docs/DFU_FLASHING.md) for DFU recovery instructions.

---

## Technical Notes

- **Radio**: Operates the on-board TI CC1101 chip directly via `furi_hal_subghz`.
- **Demo Mode**: If the CC1101 is busy (another app is using it), the app runs in demo mode with simulated-but-realistic RSSI values so the UI is always functional.
- **Stack size**: 2048 bytes (set in `application.fam`); increase to 4096 if you add SD card logging.
- **Update rate**: 100 ms (10 Hz) – low enough to avoid battery drain, fast enough for live metrics.

---

## Mapping to HackRF CLI Tools

| HackRF CLI | HackRF Companion Feature |
|------------|--------------------------|
| `hackrf_sweep` | **Scanner** view – spectrum sweep |
| `hackrf_transfer -r` | **Monitor** view – RSSI capture |
| `hackrf_biast` | Gain setting in **Settings** |
| `hackrf_clock` | Frequency preset in **Settings** |
| `hackrf_info` | **Dashboard** device info header |

---

## License

MIT – see root [LICENSE](../../LICENSE) file.
