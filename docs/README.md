# Documentation Directory

Welcome to the FlipperZero Custom Firmware documentation!

## Documentation Overview

This directory contains comprehensive guides and resources to help you work with the custom firmware.

### 📖 Available Guides

| Document | Description | Best For |
|----------|-------------|----------|
| **[Quick Start Guide](QUICK_START.md)** | Step-by-step setup instructions | New users getting started |
| **[FAQ](FAQ.md)** | Frequently asked questions | Quick answers to common questions |
| **[Application Development](APPLICATION_DEVELOPMENT.md)** | Complete app development guide | Developers creating custom apps |

### 🔗 Other Important Documents

Located in the root directory:

- **[README.md](../README.md)** - Project overview and features
- **[HELP.md](../HELP.md)** - Comprehensive troubleshooting guide
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - How to contribute to the project

## Where to Start?

### I'm brand new to this project
👉 Start with **[Quick Start Guide](QUICK_START.md)**

### I'm having issues
👉 Check **[HELP.md](../HELP.md)** troubleshooting guide

### I have a question
👉 Browse the **[FAQ](FAQ.md)**

### I want to create an application
👉 Read **[Application Development](APPLICATION_DEVELOPMENT.md)**

### I want to contribute
👉 See **[CONTRIBUTING.md](../CONTRIBUTING.md)**

## Documentation Structure

```
FlipperZero-CustomFirmware/
├── README.md                      # Project overview
├── HELP.md                        # Troubleshooting guide
├── CONTRIBUTING.md                # Contribution guidelines
└── docs/                          # Additional documentation
    ├── README.md                  # This file
    ├── QUICK_START.md            # Getting started guide
    ├── FAQ.md                    # Frequently asked questions
    └── APPLICATION_DEVELOPMENT.md # App development guide
```

## Finding Information

### By Topic

- **Setup & Installation**: [Quick Start](QUICK_START.md) → Prerequisites section
- **Building**: [Quick Start](QUICK_START.md) → Build section
- **Auto-Start**: [FAQ](FAQ.md) → Auto-Start Feature section
- **Troubleshooting**: [HELP.md](../HELP.md) → Common Issues section
- **Development**: [Application Development](APPLICATION_DEVELOPMENT.md)
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md)

### By Task

| I want to... | Read this |
|--------------|-----------|
| Set up the environment | [Quick Start](QUICK_START.md) |
| Build and flash firmware | [Quick Start](QUICK_START.md) Step 5-6 |
| Fix a build error | [HELP.md](../HELP.md) Building Firmware section |
| Create my first app | [Application Development](APPLICATION_DEVELOPMENT.md) Quick Start |
| Debug an application | [Application Development](APPLICATION_DEVELOPMENT.md) Debugging section |
| Configure auto-start | [FAQ](FAQ.md) Auto-Start Feature section |
| Report a bug | [Issue Templates](../.github/ISSUE_TEMPLATE/) |
| Contribute code | [CONTRIBUTING.md](../CONTRIBUTING.md) |

## Document Conventions

Throughout the documentation:

- 📖 - Documentation reference
- 💡 - Tip or helpful information
- ⚠️ - Warning or important note
- ✅ - Success or completed item
- ❌ - Error or failed item
- 🚀 - New feature or exciting capability
- 🔧 - Configuration or settings
- 🐛 - Bug or issue

### Code Examples

```bash
# Command line examples look like this
./fbt build
```

```c
// C code examples look like this
int32_t my_app_main(void* p) {
    return 0;
}
```

```python
# Python code examples look like this
LOADER_AUTOSTART = "My App"
```

## Keeping Documentation Updated

Documentation is a living resource. If you find:

- Outdated information
- Missing details
- Broken links
- Unclear explanations
- Opportunities for improvement

Please help us improve! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing documentation improvements.

## Quick Reference

### Essential Commands

```bash
# Setup
./startup.sh                          # Initial setup

# Building
./fbt                                 # Build firmware
./fbt clean                          # Clean build
./fbt flash_usb                      # Flash to device

# Development
screen /dev/ttyACM0 115200          # Serial console
```

### Essential Files

```
applications_user/*/application.fam   # App manifest
build_configs/fbt_options.py         # Build configuration
```

### Essential Settings

```python
# In fbt_options.py
LOADER_AUTOSTART = "App Name"        # Auto-start app
DEBUG = 1                            # Debug mode
COMPACT = 1                          # Size optimization
```

## External Resources

- [Flipper Zero Official Documentation](https://docs.flipperzero.one/)
- [Unleashed Firmware](https://github.com/DarkFlippers/unleashed-firmware)
- [FBT Documentation](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/fbt.md)
- [Flipper Zero Discord](https://flipperzero.one/discord)

## Getting Help

Can't find what you need?

1. **Search** - Use GitHub's search to find relevant issues/discussions
2. **Ask** - Open a new issue using our [help template](../.github/ISSUE_TEMPLATE/help_question.yml)
3. **Community** - Join the Flipper Zero Discord community

## Feedback

Your feedback helps improve this documentation!

- 👍 Found it helpful? Star the repository!
- 📝 Found an issue? [Open an issue](https://github.com/NaTo1000/FlipperZero-CustomFirmware/issues)
- 💡 Have suggestions? [Start a discussion](https://github.com/NaTo1000/FlipperZero-CustomFirmware/discussions)

---

**Thank you for using FlipperZero Custom Firmware!** 🚀
