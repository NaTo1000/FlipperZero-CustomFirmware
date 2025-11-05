# Development Environment Setup Guide

This guide will help you set up an optimal development environment for FlipperZero Custom Firmware development.

## Table of Contents

- [Prerequisites](#prerequisites)
- [System Dependencies](#system-dependencies)
- [Python Environment](#python-environment)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Development Workflow](#development-workflow)
- [Common Issues](#common-issues)

## Prerequisites

### Operating System

- **Linux**: Ubuntu 20.04+, Debian 11+, or equivalent
- **macOS**: 12.0+ (Monterey or later)
- **Windows**: WSL2 with Ubuntu 20.04+

### Required Tools

1. **Git** (version 2.30+)
2. **Python** (3.11 or 3.12)
3. **Build tools** (gcc, make, etc.)

## System Dependencies

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    gcc-arm-none-eabi \
    dfu-util \
    ccache \
    cmake \
    ninja-build
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install git python cmake ninja dfu-util ccache
brew install --cask gcc-arm-embedded
```

### Windows (WSL2)

First, install WSL2 with Ubuntu:

```powershell
wsl --install -d Ubuntu-22.04
```

Then follow the Ubuntu/Debian instructions above.

## Python Environment

### 1. Clone the Repository

```bash
git clone https://github.com/NaTo1000/FlipperZero-CustomFirmware.git
cd FlipperZero-CustomFirmware
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

For general development:

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

For full development environment with additional tools:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 4. Verify Installation

```bash
# Check installed packages
pip list

# Verify dependency tree
pip install pipdeptree
pipdeptree

# Check for package conflicts
pip check
```

## Pre-commit Hooks

Pre-commit hooks help maintain code quality by running checks before each commit.

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# (Optional) Run against all files initially
pre-commit run --all-files
```

### What Gets Checked

- **Code Formatting**: Black, isort
- **Linting**: flake8, bandit (security)
- **File Checks**: Trailing whitespace, file endings, YAML syntax
- **Security**: Private key detection

### Manual Execution

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Update hook versions
pre-commit autoupdate
```

## Development Workflow

### 1. Start Development Session

```bash
# Activate virtual environment
source .venv/bin/activate

# Update dependencies if needed
pip install -r requirements.txt --upgrade
```

### 2. Code Development

```bash
# Format code
black build_configs/

# Sort imports
isort build_configs/

# Run linters
flake8 build_configs/

# Type checking
mypy build_configs/ --ignore-missing-imports
```

### 3. Security Checks

```bash
# Check for vulnerabilities in dependencies
pip-audit

# Security linting of code
bandit -r build_configs/
```

### 4. Testing

```bash
# Run tests (if available)
pytest

# With coverage
pytest --cov=build_configs --cov-report=html
```

### 5. Commit Changes

With pre-commit hooks installed, checks run automatically:

```bash
git add .
git commit -m "Your commit message"
```

## Common Issues

### Issue: Import errors for installed packages

**Solution**: Make sure virtual environment is activated:

```bash
source .venv/bin/activate
which python  # Should point to .venv/bin/python
```

### Issue: pip install fails with permission errors

**Solution**: Use virtual environment instead of system Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: Pre-commit hooks failing

**Solution**: Update hooks and run manually:

```bash
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### Issue: Black and flake8 conflicts

**Solution**: Use compatible configurations:

- Black line length: 100
- flake8 ignores: E203, W503

These are already configured in `.pre-commit-config.yaml`.

### Issue: ARM toolchain not found

**Ubuntu/Debian**:
```bash
sudo apt install gcc-arm-none-eabi
```

**macOS**:
```bash
brew install --cask gcc-arm-embedded
```

## Environment Variables

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Enable pip user installs
export PIP_USER=1

# Python cache
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1

# Color output
export CLICOLOR=1
export FORCE_COLOR=1
```

## Continuous Integration

The CI pipeline runs automatically on:

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

### CI Jobs

1. **Python Linting & Code Quality**: Multi-version Python testing (3.11, 3.12)
2. **Security & Dependency Scanning**: pip-audit, bandit
3. **Validate Requirements**: Installation verification, dependency tree
4. **Validate Project Structure**: File checks, syntax validation
5. **Generate Documentation**: Workflow documentation

### Viewing CI Results

- Check GitHub Actions tab
- Download artifacts (reports, documentation)
- Review security scan results

## Additional Resources

- [Flipper Zero Documentation](https://docs.flipperzero.one/)
- [Unleashed Firmware](https://github.com/DarkFlippers/unleashed-firmware)
- [FBT Documentation](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/fbt.md)
- [Python Packaging Guide](https://packaging.python.org/)
- [Pre-commit Framework](https://pre-commit.com/)

## Getting Help

If you encounter issues:

1. Check this guide first
2. Review the README.md
3. Check GitHub Issues
4. Review CI logs for similar errors

## Updating This Guide

This guide should be updated when:

- New dependencies are added
- System requirements change
- Development workflow improves
- Common issues are discovered

Last updated: 2025-11-05
