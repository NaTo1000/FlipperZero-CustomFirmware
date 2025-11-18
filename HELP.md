# Getting Help with FlipperZero Custom Firmware

Welcome! This guide will help you troubleshoot common issues and get started with the FlipperZero Custom Firmware project.

## Quick Links

- [Common Issues](#common-issues)
- [Troubleshooting](#troubleshooting)
- [FAQ](#frequently-asked-questions)
- [Getting Support](#getting-support)

## Common Issues

### Setup and Installation

#### Issue: "Python 3.8+ required" error
**Solution:**
```bash
# Check your Python version
python3 --version

# If version is < 3.8, install Python 3.8+
# On Ubuntu/Debian:
sudo apt install python3.11

# On macOS:
brew install python@3.11
```

#### Issue: Virtual environment activation fails
**Solution:**
```bash
# Make sure you're in the project directory
cd FlipperZero-CustomFirmware

# Remove old venv if corrupted
rm -rf .venv

# Create fresh virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate  # Windows
```

#### Issue: startup.sh permission denied
**Solution:**
```bash
# Make the script executable
chmod +x startup.sh

# Then run it
./startup.sh
```

### Building Firmware

#### Issue: "unleashed-firmware not found"
**Solution:**
The custom firmware requires the base Unleashed firmware. Clone it:
```bash
# From the parent directory of FlipperZero-CustomFirmware
cd ..
git clone https://github.com/DarkFlippers/unleashed-firmware.git
cd unleashed-firmware
git submodule update --init --recursive
```

#### Issue: FBT build fails
**Solution:**
```bash
# Make sure you're in the unleashed-firmware directory
cd unleashed-firmware

# Clean previous builds
./fbt clean

# Try building again
./fbt
```

#### Issue: "ARM GCC toolchain not found"
**Solution:**
The FBT tool will automatically download the toolchain on first run. If it fails:
```bash
# Remove cached toolchain
rm -rf ~/.fbt

# Run FBT again - it will re-download
./fbt
```

### Application Development

#### Issue: Custom application not appearing in menu
**Solution:**
1. Ensure your application.fam is properly configured
2. Rebuild the firmware completely:
```bash
./fbt clean
./fbt
```
3. Flash to device:
```bash
./fbt flash_usb
```

#### Issue: Auto-start not working
**Solution:**
1. Check that `LOADER_AUTOSTART` in `fbt_options.py` matches your app name EXACTLY:
```python
LOADER_AUTOSTART = "Autostart Test"  # Must match application.fam name
```
2. The name must match the `name` field in `application.fam`:
```python
App(
    name="Autostart Test",  # This exact name
    ...
)
```
3. Rebuild and reflash the firmware

#### Issue: Application crashes on device
**Solution:**
1. Check stack size in application.fam - increase if needed:
```python
stack_size=2048,  # Increase from 1024
```
2. Enable debug mode in fbt_options.py:
```python
DEBUG = 1
```
3. Use serial console to view crash logs:
```bash
screen /dev/ttyACM0 115200
```

### Flashing and Device Connection

#### Issue: Device not detected (Linux)
**Solution:**
```bash
# Add udev rules for Flipper Zero
sudo bash -c 'cat > /etc/udev/rules.d/42-flipperzero.rules << EOF
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", TAG+="uaccess"
EOF'

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Reconnect your Flipper Zero
```

#### Issue: Flash fails with "Device busy"
**Solution:**
1. Disconnect and reconnect the device
2. Make sure no other programs are accessing the serial port:
```bash
# Check what's using the port
lsof | grep ttyACM
```
3. Close any terminal/serial programs (screen, minicom, etc.)

#### Issue: Firmware update stuck
**Solution:**
1. Put device in DFU mode manually:
   - Power off the Flipper Zero
   - Hold LEFT + BACK buttons
   - While holding, connect USB
   - Release buttons when device vibrates
2. Try flashing again:
```bash
./fbt flash_usb_full
```

## Troubleshooting

### Debug Mode

Enable detailed logging by setting debug mode in `fbt_options.py`:
```python
DEBUG = 1
```

### Serial Console

View real-time logs from your Flipper Zero:
```bash
# Linux/macOS
screen /dev/ttyACM0 115200

# Exit screen: Ctrl+A, then K

# Alternative with minicom
minicom -D /dev/ttyACM0 -b 115200
```

### Build Clean Start

If you encounter persistent build issues:
```bash
# Complete clean rebuild
cd unleashed-firmware
./fbt clean
rm -rf build/ dist/
./fbt
```

### Checking Application Files

Verify your application structure:
```
applications_user/
└── your_app/
    ├── application.fam    # Manifest file (required)
    └── your_app.c         # Main source file (required)
```

Minimum application.fam content:
```python
App(
    appid="your_app_id",           # Unique identifier
    name="Your App Name",          # Display name
    apptype=FlipperAppType.EXTERNAL,
    entry_point="your_app_main",   # Function name in .c file
    sources=["your_app.c"],        # Source files
    stack_size=1024,               # Stack size in bytes
)
```

## Frequently Asked Questions

### Q: What firmware version is this based on?
A: This custom firmware is based on the Unleashed firmware, which is itself based on the official Flipper Zero firmware.

### Q: Will this void my warranty?
A: Custom firmware modifications may void warranties. Use at your own risk.

### Q: Can I revert to official firmware?
A: Yes! You can always flash the official firmware using qFlipper or the Flipper Mobile app.

### Q: How do I update to the latest version?
A:
```bash
# Update this repository
cd FlipperZero-CustomFirmware
git pull

# Update unleashed-firmware
cd ../unleashed-firmware
git pull
git submodule update --init --recursive

# Copy updated files
cp -r ../FlipperZero-CustomFirmware/applications_user/* applications_user/
cp ../FlipperZero-CustomFirmware/build_configs/fbt_options.py .

# Rebuild
./fbt clean
./fbt
./fbt flash_usb
```

### Q: Why is my binary so large?
A: Debug builds are larger. For production:
```python
# In fbt_options.py
DEBUG = 0
COMPACT = 1
```

### Q: Can I run multiple auto-start apps?
A: No, only one app can auto-start. Choose the most important one.

### Q: How do I add custom icons?
A: Place PNG files in your app directory and reference them in application.fam:
```python
fap_icon="my_icon.png",
```

## Getting Support

### Before Asking for Help

1. **Check this guide** - Most common issues are covered here
2. **Search existing issues** - Your problem might already be solved
3. **Read the README** - Basic setup and usage instructions
4. **Check the logs** - Serial console often shows the exact problem

### How to Ask for Help

When opening an issue, please include:

1. **What you're trying to do** - Be specific about your goal
2. **What you've tried** - List the steps you've taken
3. **Error messages** - Full error text, not just "it doesn't work"
4. **Your environment**:
   - Operating system and version
   - Python version (`python3 --version`)
   - Git version (`git --version`)
   - Flipper Zero hardware revision
5. **Relevant files** - Share your application.fam and fbt_options.py if relevant

### Where to Get Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general help
- **Flipper Zero Community**: Discord and forums for general Flipper questions

### Example of a Good Issue

```
Title: Auto-start not working after following setup guide

Environment:
- OS: Ubuntu 22.04
- Python: 3.11.2
- Flipper Zero: Hardware revision 7

Problem:
I've followed the setup guide but my custom app doesn't auto-start.

What I've tried:
1. Verified LOADER_AUTOSTART matches app name exactly
2. Rebuilt firmware with ./fbt clean && ./fbt
3. Flashed successfully with ./fbt flash_usb
4. Device boots normally but goes to main menu instead of my app

Error messages:
No errors during build or flash. Serial console shows:
[loader] Starting default app

Files:
application.fam: [paste content]
fbt_options.py LOADER_AUTOSTART setting: [paste line]

Question:
What am I missing in the auto-start configuration?
```

## Additional Resources

- [Flipper Zero Official Docs](https://docs.flipperzero.one/)
- [Unleashed Firmware GitHub](https://github.com/DarkFlippers/unleashed-firmware)
- [FBT Documentation](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/fbt.md)
- [Flipper Development Discord](https://flipperzero.one/discord)

## Contributing

If you've solved a problem not listed here, please contribute! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Still stuck?** Open an issue with detailed information, and the community will help!
