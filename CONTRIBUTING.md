# Contributing to FlipperZero Custom Firmware

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or inflammatory comments
- Publishing others' private information
- Any conduct that would be inappropriate in a professional setting

## Getting Started

### Prerequisites

1. **Development Environment**:
   - Linux, macOS, or WSL2 on Windows
   - Python 3.8 or higher
   - Git 2.0 or higher
   - Basic knowledge of C programming
   - Flipper Zero device (recommended for testing)

2. **Set Up Your Environment**:
   ```bash
   # Fork the repository on GitHub
   # Clone your fork
   git clone https://github.com/YOUR_USERNAME/FlipperZero-CustomFirmware.git
   cd FlipperZero-CustomFirmware
   
   # Run setup script
   ./startup.sh
   
   # Clone base firmware
   cd ..
   git clone https://github.com/DarkFlippers/unleashed-firmware.git
   cd unleashed-firmware
   git submodule update --init --recursive
   ```

3. **Add Upstream Remote**:
   ```bash
   cd FlipperZero-CustomFirmware
   git remote add upstream https://github.com/NaTo1000/FlipperZero-CustomFirmware.git
   ```

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check if the issue already exists
2. Verify it's not a problem with the base Unleashed firmware
3. Test with the latest version

When reporting a bug, include:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, hardware revision)
- Error messages and logs
- Screenshots if applicable

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:
1. Check if it's already been suggested
2. Provide a clear use case
3. Explain why it would be useful
4. Consider potential drawbacks
5. Offer to help implement it

### Contributing Code

We welcome:
- Bug fixes
- New custom applications
- Documentation improvements
- Build system enhancements
- Testing improvements

## Development Workflow

### 1. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation if needed

### 3. Test Your Changes

```bash
# Test application builds
cd ../unleashed-firmware
cp -r ../FlipperZero-CustomFirmware/applications_user/* applications_user/
./fbt

# Test on device if possible
./fbt flash_usb
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add new auto-start configuration option"
```

#### Commit Message Format

Use conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add support for multiple auto-start configurations
fix: resolve startup script Python version detection
docs: update troubleshooting guide with serial console info
style: format fbt_options.py with black
refactor: simplify application.fam template
test: add validation for application manifest files
chore: update Python dependencies
```

### 5. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Coding Standards

### Python Code

We use `black` and `isort` for Python formatting:

```bash
# Format code
black build_configs/
isort build_configs/

# Check formatting
black --check build_configs/
isort --check-only build_configs/
```

Python style guidelines:
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small
- Use type hints where appropriate

### C Code (Applications)

Follow Flipper Zero SDK conventions:
- Use `snake_case` for functions and variables
- Use `PascalCase` for types and structs
- Include proper header guards
- Free allocated resources
- Handle errors appropriately

Example:
```c
typedef struct {
    Gui* gui;
    ViewPort* view_port;
    bool running;
} MyApp;

static void my_app_render_callback(Canvas* canvas, void* context) {
    MyApp* app = context;
    // Implementation
}

int32_t my_app_main(void* p) {
    // Proper resource management
    MyApp* app = malloc(sizeof(MyApp));
    
    // ... application logic ...
    
    // Clean up
    free(app);
    return 0;
}
```

### Documentation

- Use clear, concise language
- Include code examples
- Keep formatting consistent
- Update table of contents when adding sections
- Test all commands and code snippets

## Testing

### Manual Testing

1. **Build Test**:
   ```bash
   cd unleashed-firmware
   ./fbt clean
   ./fbt
   ```

2. **Application Test**:
   - Install on device
   - Test all functionality
   - Verify auto-start (if applicable)
   - Check error handling
   - Test exit/cleanup

3. **Documentation Test**:
   - Verify all links work
   - Test all code examples
   - Check formatting renders correctly

### CI/CD

Our CI pipeline automatically:
- Lints Python code
- Validates file structure
- Checks for security vulnerabilities

Ensure your changes pass CI before requesting review.

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main
- [ ] Changes are minimal and focused

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why are these changes needed?

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
How were these changes tested?

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tested on device (if applicable)
- [ ] CI passes
```

### Review Process

1. Maintainer reviews your PR
2. Address any requested changes
3. Update your branch if needed
4. Once approved, maintainer will merge

### After Merge

```bash
# Update your local repository
git checkout main
git pull upstream main

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## Project Structure

```
FlipperZero-CustomFirmware/
├── .github/              # GitHub configuration
│   └── workflows/        # CI/CD workflows
├── applications_user/    # Custom applications
│   └── app_name/
│       ├── application.fam   # App manifest
│       └── app_name.c        # App source code
├── build_configs/        # Build configurations
│   └── fbt_options.py    # FBT build options
├── docs/                 # Additional documentation
├── CONTRIBUTING.md       # This file
├── HELP.md              # Troubleshooting guide
├── README.md            # Project overview
├── requirements.txt     # Python dependencies
└── startup.sh           # Setup script
```

### Adding a New Application

1. Create directory in `applications_user/`:
   ```bash
   mkdir applications_user/my_app
   ```

2. Create `application.fam`:
   ```python
   App(
       appid="my_app",
       name="My App",
       apptype=FlipperAppType.EXTERNAL,
       entry_point="my_app_main",
       sources=["my_app.c"],
       fap_category="Misc",
       stack_size=1024,
   )
   ```

3. Create `my_app.c` with entry point
4. Test build and functionality
5. Document in README if significant

## Questions?

If you have questions not covered here:
- Check [HELP.md](HELP.md) for troubleshooting
- Open a discussion on GitHub
- Ask in Flipper Zero community Discord

## Recognition

Contributors will be:
- Listed in project documentation
- Credited in release notes
- Appreciated by the community!

Thank you for contributing to FlipperZero Custom Firmware! 🚀
