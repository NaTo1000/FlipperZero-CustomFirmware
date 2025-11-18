# Quick Start Guide

Get up and running with FlipperZero Custom Firmware in minutes!

## Prerequisites Check

Before starting, ensure you have:
- [ ] Python 3.8 or higher
- [ ] Git
- [ ] USB cable for Flipper Zero
- [ ] 20GB+ free disk space
- [ ] 1 hour for initial setup

## Step 1: Clone This Repository

```bash
# Clone the repository
git clone https://github.com/NaTo1000/FlipperZero-CustomFirmware.git
cd FlipperZero-CustomFirmware
```

## Step 2: Run Setup Script

```bash
# Make script executable (if needed)
chmod +x startup.sh

# Run setup
./startup.sh
```

This script will:
- ✅ Check Python version
- ✅ Check Git installation
- ✅ Create virtual environment
- ✅ Install Python dependencies

## Step 3: Clone Base Firmware

```bash
# Go to parent directory
cd ..

# Clone Unleashed firmware
git clone https://github.com/DarkFlippers/unleashed-firmware.git
cd unleashed-firmware

# Initialize submodules (this takes a while!)
git submodule update --init --recursive
```

☕ **Note**: Submodule initialization can take 10-30 minutes depending on your internet connection.

## Step 4: Copy Custom Files

```bash
# Copy custom applications
cp -r ../FlipperZero-CustomFirmware/applications_user/* applications_user/

# Copy build configuration
cp ../FlipperZero-CustomFirmware/build_configs/fbt_options.py .
```

## Step 5: Build Firmware

```bash
# Build firmware (first build takes 20-60 minutes)
./fbt
```

The first build will:
- Download ARM GCC toolchain
- Download dependencies
- Compile firmware
- Create flashable files

☕ **Tip**: First build is slow, subsequent builds are much faster (5-15 minutes).

## Step 6: Flash to Device

### Option A: Flash via USB (Recommended)

```bash
# Connect Flipper Zero via USB
# Flash firmware
./fbt flash_usb
```

### Option B: Manual Flash via qFlipper

1. Build the firmware: `./fbt`
2. Find the `.dfu` file in `dist/f7/` directory
3. Open qFlipper
4. Connect Flipper Zero
5. Install from file → Select `.dfu` file

## Step 7: Verify Installation

1. **Disconnect and restart** your Flipper Zero
2. The custom app should **auto-start** on boot
3. You should see "Autostart Test" application
4. Press **BACK** button to exit to main menu

## Success! 🎉

Your Flipper Zero is now running custom firmware with auto-start capabilities!

## What's Next?

### Explore the Auto-Start App

The included example app demonstrates:
- Auto-starting on boot
- Basic GUI rendering
- Input handling
- Proper cleanup and exit

### Create Your Own App

Follow the [Application Development Guide](APPLICATION_DEVELOPMENT.md) to create your first custom application.

### Customize Auto-Start

Edit `fbt_options.py` to change which app starts on boot:
```python
LOADER_AUTOSTART = "Your App Name"
```

Then rebuild and reflash:
```bash
./fbt clean
./fbt
./fbt flash_usb
```

## Common First-Time Issues

### "Python 3.8+ required"

**Solution**: Install newer Python version
```bash
# Ubuntu/Debian
sudo apt install python3.11

# macOS
brew install python@3.11
```

### "Device not detected" (Linux)

**Solution**: Add udev rules
```bash
sudo bash -c 'cat > /etc/udev/rules.d/42-flipperzero.rules << EOF
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", TAG+="uaccess"
EOF'

sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Build fails with toolchain errors

**Solution**: Clean and retry
```bash
rm -rf ~/.fbt
./fbt clean
./fbt
```

### Auto-start doesn't work

**Solution**: Verify exact name match
1. Check `application.fam` name field
2. Check `fbt_options.py` LOADER_AUTOSTART
3. Must match exactly (case-sensitive)
4. Rebuild after changes

## Development Workflow

Once set up, your typical workflow is:

1. **Edit** application in `applications_user/`
2. **Copy** to unleashed-firmware directory
3. **Build**: `./fbt`
4. **Flash**: `./fbt flash_usb`
5. **Test** on device
6. **Repeat** as needed

### Quick Rebuild Command

```bash
# One-liner for quick iteration
cp -r ../FlipperZero-CustomFirmware/applications_user/* applications_user/ && ./fbt && ./fbt flash_usb
```

## Useful Commands

### Build Commands

```bash
# Regular build
./fbt

# Clean build
./fbt clean

# Build specific app
./fbt fap_myapp

# Build and flash
./fbt flash_usb
```

### Serial Console (for debugging)

```bash
# View logs from device
screen /dev/ttyACM0 115200

# Exit screen: Ctrl+A then K
```

### Check Device Info

On your Flipper Zero:
1. Settings → System Info
2. Note hardware revision
3. Note firmware version

## Additional Resources

- **[README.md](../README.md)** - Project overview
- **[HELP.md](../HELP.md)** - Troubleshooting guide
- **[FAQ](FAQ.md)** - Common questions
- **[Application Development](APPLICATION_DEVELOPMENT.md)** - Create apps
- **[Contributing](../CONTRIBUTING.md)** - Contribute to project

## Getting Help

If you get stuck:

1. **Check [HELP.md](../HELP.md)** - Most issues covered there
2. **Check [FAQ](FAQ.md)** - Common questions answered
3. **Search issues** - Your problem might be solved
4. **Open issue** - Use "Help / Question" template

## Updating Later

To update to the latest version:

```bash
# Update this repo
cd FlipperZero-CustomFirmware
git pull

# Update unleashed-firmware
cd ../unleashed-firmware
git pull
git submodule update --init --recursive

# Copy updated files
cp -r ../FlipperZero-CustomFirmware/applications_user/* applications_user/
cp ../FlipperZero-CustomFirmware/build_configs/fbt_options.py .

# Clean rebuild
./fbt clean
./fbt
./fbt flash_usb
```

## Troubleshooting Build

If build fails:

```bash
# Complete clean rebuild
cd unleashed-firmware
./fbt clean
rm -rf build/ dist/ .sconsign.dblite
rm -rf ~/.fbt  # Removes toolchain cache
./fbt
```

## Need More Help?

- **Detailed Troubleshooting**: See [HELP.md](../HELP.md)
- **Common Questions**: See [FAQ](FAQ.md)
- **Report Issues**: Use GitHub issue templates
- **Community**: Flipper Zero Discord

---

**Congratulations on getting started! 🚀**

You're now ready to develop and deploy custom applications for your Flipper Zero!
