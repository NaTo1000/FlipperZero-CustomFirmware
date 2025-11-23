# Frequently Asked Questions (FAQ)

## General Questions

### What is this project?

This project provides custom firmware modifications and applications for the Flipper Zero device, built on top of the Unleashed firmware. It features automatic application launching on boot, custom applications, and enhanced system functionality.

### Is this official firmware?

No, this is a community-developed custom firmware built on top of the Unleashed firmware, which itself is based on the official Flipper Zero firmware.

### Will this void my warranty?

Installing custom firmware may void your warranty. Always check your warranty terms and understand the risks before modifying your device.

### Can I brick my Flipper Zero?

The Flipper Zero has robust recovery mechanisms. Even if something goes wrong, you can usually recover by:
1. Entering DFU mode (hold LEFT + BACK, then connect USB)
2. Using qFlipper to restore official firmware
3. Using the mobile app to reinstall firmware

However, always back up your data and proceed carefully.

### Can I go back to official firmware?

Yes! You can always return to official firmware using:
- **qFlipper**: Official desktop application
- **Mobile App**: Flipper Mobile app for iOS/Android
- **Web Updater**: Online firmware flasher

## Setup and Installation

### What operating systems are supported?

- **Linux**: Fully supported (Ubuntu, Debian, Fedora, Arch, etc.)
- **macOS**: Fully supported (Intel and Apple Silicon)
- **Windows**: Supported via WSL2 (Windows Subsystem for Linux)

### What are the system requirements?

Minimum:
- 4GB RAM
- 10GB free disk space
- USB port for device connection
- Python 3.8 or higher
- Git

Recommended:
- 8GB+ RAM
- 20GB+ free disk space
- USB 2.0 or higher
- Python 3.11+

### How long does the setup take?

- Initial setup: 5-10 minutes
- Firmware clone and build: 30-60 minutes (first time)
- Subsequent builds: 5-15 minutes

### Do I need a Flipper Zero to develop?

Not for basic development, but highly recommended for:
- Testing applications
- Verifying auto-start functionality
- Debugging hardware-specific issues
- Final validation before release

## Building and Flashing

### How do I build the firmware?

```bash
# Navigate to unleashed-firmware directory
cd unleashed-firmware

# Build firmware
./fbt
```

### How do I flash to my device?

```bash
# Via USB (recommended)
./fbt flash_usb

# Or full flash (includes radio stack)
./fbt flash_usb_full
```

### How long does building take?

- First build: 20-60 minutes (downloads toolchain and dependencies)
- Incremental builds: 2-10 minutes
- Clean builds: 5-15 minutes

### Can I build for specific hardware versions?

Yes, set `TARGET_HW` in `fbt_options.py`:
```python
TARGET_HW = 7  # For Flipper Zero hardware revision 7
```

Check your hardware revision in Settings → System Info on your device.

### What's the difference between debug and release builds?

**Debug builds**:
- Larger binary size
- Include debug symbols
- Better error messages
- Slower performance
- Easier to debug issues

**Release builds**:
```python
# In fbt_options.py
DEBUG = 0
COMPACT = 1
```
- Smaller binary size
- Optimized performance
- No debug symbols
- Production-ready

## Custom Applications

### How do I create a custom application?

1. Create directory: `applications_user/myapp/`
2. Create `application.fam` manifest
3. Create `myapp.c` source file
4. Build and test

See [Application Development Guide](APPLICATION_DEVELOPMENT.md) for details.

### What programming language do I use?

Applications are written in **C** using the Flipper Zero SDK/API.

### Where can I find API documentation?

- [Official Flipper Docs](https://docs.flipperzero.one/)
- Unleashed firmware source code
- Example applications in `applications/` directory
- Community Discord and forums

### How much memory do applications have?

- Default stack: 1024 bytes
- Can be increased in `application.fam`:
  ```python
  stack_size=2048,  # Increase as needed
  ```
- Maximum depends on available RAM and other running services

### Can I use external libraries?

Limited. You can:
- Use libraries provided by the SDK
- Include lightweight, compatible C libraries
- Statically link appropriate libraries

Cannot easily use:
- Large libraries (memory constraints)
- Libraries requiring OS features not available
- Libraries incompatible with ARM Cortex-M4

## Auto-Start Feature

### What is auto-start?

Auto-start allows an application to launch automatically when the Flipper Zero boots up, bypassing the main menu.

### How do I enable auto-start?

In `fbt_options.py`:
```python
LOADER_AUTOSTART = "Your App Name"
```

The name must match **exactly** with the `name` field in your `application.fam`.

### Can I auto-start multiple applications?

No, only one application can auto-start. Choose your primary application.

### How do I disable auto-start?

Comment out or remove the line in `fbt_options.py`:
```python
# LOADER_AUTOSTART = "Your App Name"
```

Then rebuild and reflash.

### Can I add a delay before auto-start?

Yes, use:
```python
LOADER_START_DELAY = 1.0  # Seconds
```

### How do I exit an auto-started application?

Implement proper back button handling in your application:
```c
if(event->type == InputTypeShort && event->key == InputKeyBack) {
    app->running = false;
}
```

After exiting, the device returns to the main menu.

## Troubleshooting

### Build fails with "No module named 'X'"

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Application doesn't appear in menu

1. Verify `application.fam` syntax
2. Rebuild: `./fbt clean && ./fbt`
3. Reflash: `./fbt flash_usb`
4. Check FBT output for errors

### Device not detected

**Linux**: Add udev rules (see [HELP.md](../HELP.md))
**macOS**: Check System Preferences → Security & Privacy
**Windows/WSL**: Use `usbipd` to attach device to WSL

### Build succeeds but application crashes

1. Check serial console for crash logs
2. Increase stack size in `application.fam`
3. Verify proper resource cleanup
4. Check for memory leaks
5. Enable debug mode for better error messages

### Changes don't take effect after rebuild

1. Do a clean build: `./fbt clean && ./fbt`
2. Verify you copied files to correct location
3. Ensure you're flashing the right build
4. Check device storage isn't full

## Development

### How do I debug applications?

1. **Serial Console**:
   ```bash
   screen /dev/ttyACM0 115200
   ```

2. **Debug Logging**:
   ```c
   FURI_LOG_I("MyApp", "Debug message");
   FURI_LOG_E("MyApp", "Error: %d", error_code);
   ```

3. **Debug Build**: Set `DEBUG = 1` in `fbt_options.py`

### Can I use an IDE?

Yes! Popular choices:
- **VS Code**: With C/C++ extension
- **CLion**: JetBrains IDE for C/C++
- **Vim/Neovim**: With appropriate plugins
- **Emacs**: With C development setup

Configure your IDE to:
- Use the ARM GCC toolchain
- Include Flipper SDK headers
- Run FBT for building

### How do I contribute back to the project?

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

### Where can I get help?

1. Check [HELP.md](../HELP.md) troubleshooting guide
2. Search existing GitHub issues
3. Open a new issue with details
4. Join Flipper Zero community Discord
5. Ask in community forums

## Firmware Questions

### What's the difference between Official, Unleashed, and this firmware?

**Official Firmware**:
- Maintained by Flipper Devices Inc.
- Conservative feature set
- Most stable and tested
- Regular updates

**Unleashed Firmware**:
- Community-enhanced fork of official
- Additional features and apps
- More frequent updates
- Some experimental features

**This Custom Firmware**:
- Built on Unleashed
- Custom applications
- Auto-start capabilities
- Specific use cases and enhancements

### How often should I update?

- **Security issues**: Update immediately
- **Bug fixes**: Update when convenient
- **New features**: Update if needed

Always check release notes before updating.

### Will my data be lost when flashing?

Generally no, but:
- Backup your data first (via qFlipper)
- Save settings screenshots
- Export important files
- Better safe than sorry!

### Can I use apps from other firmwares?

Sometimes, but:
- Apps built for official firmware may not work
- API compatibility varies between versions
- Test thoroughly before deploying
- When in doubt, rebuild from source

## Performance and Optimization

### Why is my firmware binary so large?

Debug builds are larger. For production:
```python
DEBUG = 0
COMPACT = 1
```

Also consider:
- Removing unused applications
- Optimizing assets
- Minimizing included libraries

### How can I reduce memory usage?

1. Reduce stack size (carefully)
2. Free resources promptly
3. Avoid large static allocations
4. Use memory pools efficiently
5. Profile memory usage with debug tools

### How can I improve build times?

1. Use incremental builds (don't `clean` unless needed)
2. Enable ccache if available
3. Use SSD storage
4. Increase RAM
5. Build on native Linux (faster than WSL)

## Safety and Legal

### Is this legal to use?

Yes, but:
- Don't use for illegal activities
- Respect regulations in your jurisdiction
- Some features may be restricted by law
- You are responsible for your usage

### Can I sell devices with this firmware?

Check the license terms. Generally:
- Open source licenses allow commercial use
- Must comply with license requirements
- Give proper attribution
- Maintain license notices

### How do I report security issues?

For security vulnerabilities:
1. Do NOT open a public issue
2. Email the maintainer privately
3. Allow time for fix before disclosure
4. Follow responsible disclosure practices

## Community

### How can I stay updated?

- Watch the GitHub repository
- Follow release notes
- Join community Discord
- Subscribe to discussions
- Check changelog regularly

### Can I request features?

Yes! Open a GitHub issue with:
- Clear description of feature
- Use case and benefits
- Willingness to contribute
- Potential implementation ideas

### How can I support the project?

- Contribute code
- Improve documentation
- Report bugs
- Help other users
- Share the project
- Star the repository

## Additional Resources

- [Main README](../README.md)
- [Help & Troubleshooting](../HELP.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Application Development Guide](APPLICATION_DEVELOPMENT.md)

---

**Have a question not answered here?** Open a discussion on GitHub!
