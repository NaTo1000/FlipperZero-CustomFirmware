# FlipperZero Custom Firmware Development

[![CI](https://github.com/NaTo1000/FlipperZero-CustomFirmware/actions/workflows/ci.yml/badge.svg)](https://github.com/NaTo1000/FlipperZero-CustomFirmware/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Custom firmware development project for Flipper Zero with auto-start capabilities and enhanced functionality.

## 📚 Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in minutes!
- **[Help & Troubleshooting](HELP.md)** - Solutions to common issues
- **[FAQ](docs/FAQ.md)** - Frequently asked questions
- **[Application Development](docs/APPLICATION_DEVELOPMENT.md)** - Create custom apps
- **[Contributing](CONTRIBUTING.md)** - Contribution guidelines

## Overview

This repository contains custom firmware modifications and applications for the Flipper Zero device, built on top of the Unleashed firmware. Features include automatic application launching on boot, custom applications, and enhanced system functionality.

## Quick Links

- **[Development Setup Guide](DEVELOPMENT.md)** - Complete guide for setting up your development environment
- **[CI/CD Pipeline](https://github.com/NaTo1000/FlipperZero-CustomFirmware/actions)** - View workflow runs and reports
- **[Requirements](requirements.txt)** - Production dependencies
- **[Dev Requirements](requirements-dev.txt)** - Development tools

## Features

- **Auto-Start Applications**: Automatic application launching on device boot
- **Custom Applications**: Purpose-built applications for specific use cases
- **Enhanced System Integration**: Deep integration with Flipper Zero hardware
- **Modular Architecture**: Easy to extend and customize
- **Build System Integration**: Seamless integration with FBT build system
- **CI/CD Pipeline**: Automated testing, linting, and security scanning
- **Pre-commit Hooks**: Code quality checks before commits

## Project Structure

```
FlipperZero-CustomFirmware/
├── applications_user/          # Custom user applications
│   └── autostart_test/        # Example auto-start application
├── build_configs/             # Build configuration files
│   └── fbt_options.py        # FBT configuration
├── .github/workflows/         # CI/CD workflows
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Project configuration
├── Makefile                  # Development task automation
├── DEVELOPMENT.md            # Development setup guide
└── README.md                 # This file
```

## Prerequisites

- **Operating System**: Linux, macOS, or WSL on Windows
- **Dependencies**:
  - Git
  - Python 3.11+ (3.12 recommended)
  - ARM GCC toolchain
  - FBT (Flipper Build Tool)
  - USB access for device flashing

See **[DEVELOPMENT.md](DEVELOPMENT.md)** for detailed setup instructions.

### Quick Setup (macOS)

```bash
# Install Homebrew dependencies
brew install git python cmake ninja dfu-util ccache

# Clone this repository
git clone https://github.com/NaTo1000/FlipperZero-CustomFirmware.git
cd FlipperZero-CustomFirmware

# Set up development environment (one command!)
make setup
source .venv/bin/activate
```

### Quick Setup (Linux/Ubuntu)

```bash
# Install system dependencies
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv build-essential

# Clone and setup
git clone https://github.com/NaTo1000/FlipperZero-CustomFirmware.git
cd FlipperZero-CustomFirmware
make setup
source .venv/bin/activate
```

## Development Workflow

This project includes a comprehensive development workflow with automated quality checks:

### Using Makefile (Recommended)

```bash
# Set up environment
make setup

# Format code
make format

# Run linters
make lint

# Run security scans
make security

# Run all checks
make check

# Install pre-commit hooks
make pre-commit

# Clean build artifacts
make clean

# Show all available commands
make help
```

### Manual Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Format code
black build_configs/
isort build_configs/

# Lint code
flake8 build_configs/
mypy build_configs/

# Security scan
pip-audit
bandit -r build_configs/
```

## Quick Start

1. **Clone the base firmware**:
   ```bash
   git clone https://github.com/DarkFlippers/unleashed-firmware.git
   cd unleashed-firmware
   git submodule update --init --recursive
   ```

2. **Copy custom applications**:
   ```bash
   cp -r ../FlipperZero-CustomFirmware/applications_user/* applications_user/
   ```

3. **Configure auto-start** (edit `fbt_options.py`):
   ```python
   LOADER_AUTOSTART = "Autostart Test"
   ```

4. **Build firmware**:
   ```bash
   ./fbt
   ```

5. **Flash to device**:
   ```bash
   ./fbt flash
   ```

## Custom Applications

### Auto-Start Test Application

A simple application that demonstrates auto-start functionality:

- Automatically launches on device boot
- Displays confirmation message
- Responds to user input
- Clean exit back to main menu

### Creating New Applications

1. Create a new directory in `applications_user/`
2. Add `application.fam` manifest file
3. Implement the application in C
4. Build and test

## Configuration

### Auto-Start Configuration

To enable auto-start for your application:

1. Set `LOADER_AUTOSTART` in `fbt_options.py`
2. Use the exact application name from `application.fam`
3. Rebuild firmware
4. Flash to device

### Build Options

Configure build options in `fbt_options.py`:
- `LOADER_AUTOSTART`: Application to start on boot
- `DEBUG`: Enable debug features
- `COMPACT`: Optimize for size

## Development Workflow

1. **Development**: Write and test applications
2. **Build**: Use FBT to build firmware
3. **Flash**: Deploy to Flipper Zero device
4. **Test**: Verify functionality on device
5. **Debug**: Use serial output for debugging

## Troubleshooting

For detailed troubleshooting information, see **[HELP.md](HELP.md)**.

### Common Issues

- **Build failures**: Check toolchain installation
- **Flash failures**: Ensure device is in DFU mode
- **Auto-start not working**: Verify application name matches exactly
- **Large binaries**: Consider size optimization flags

### Debug Output

Enable serial debugging to monitor application behavior:
```bash
# View logs during development
screen /dev/ttyACM0 115200
```

### Need More Help?

- 📖 [Comprehensive Troubleshooting Guide](HELP.md)
- ❓ [Frequently Asked Questions](docs/FAQ.md)
- 💬 [Open an Issue](https://github.com/NaTo1000/FlipperZero-CustomFirmware/issues/new/choose)

## Contributing

We welcome contributions! Please see **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed guidelines.

Quick summary:
1. Fork this repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on hardware
5. Submit a pull request

## Hardware Compatibility

- **Flipper Zero**: All revisions
- **Firmware Base**: Unleashed firmware
- **Memory Requirements**: Optimized for device constraints

## License

MIT License - See LICENSE file for details

## Disclaimer

**Important**: Custom firmware modifications can potentially damage your device or void warranties. Use at your own risk. Always test thoroughly and have recovery options available.

## Resources

- [Flipper Zero Documentation](https://docs.flipperzero.one/)
- [Unleashed Firmware](https://github.com/DarkFlippers/unleashed-firmware)
- [FBT Documentation](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/fbt.md)

## Author

Nathan Te-Aotonga (NaTo1000)

---

**Note**: This project is independent and not officially affiliated with Flipper Devices Inc.