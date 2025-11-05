# Quick Reference Card

## One-Time Setup

```bash
# Clone repository
git clone https://github.com/NaTo1000/FlipperZero-CustomFirmware.git
cd FlipperZero-CustomFirmware

# Set up environment (one command!)
make setup

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

## Daily Workflow

```bash
# Start your day
source .venv/bin/activate

# Before coding
git pull origin main

# While coding
make format              # Auto-format your code
make lint               # Check code quality

# Before committing
make check              # Run all checks (lint + test + security)
git add .
git commit -m "Your message"
git push
```

## Common Commands

### Code Quality
```bash
make format         # Format with black + isort
make lint           # Run all linters
make test           # Run tests with pytest
make security       # Security scans (pip-audit + bandit)
make check          # All of the above
```

### Environment Management
```bash
make setup          # Initial setup
make install        # Install prod dependencies
make install-dev    # Install dev dependencies
make clean          # Clean artifacts
```

### Dependency Management
```bash
make deps-tree      # Show dependency tree
make deps-outdated  # Check for updates
pip list            # List installed packages
```

### Pre-commit Hooks
```bash
make pre-commit     # Install hooks
pre-commit run --all-files  # Run manually
```

### Information
```bash
make help           # Show all commands
make info           # Project information
```

## File Structure

```
FlipperZero-CustomFirmware/
├── .github/workflows/ci.yml      # CI/CD pipeline
├── .pre-commit-config.yaml       # Pre-commit hooks
├── pyproject.toml               # Project config
├── Makefile                     # Development commands
├── requirements.txt             # Production deps
├── requirements-dev.txt         # Dev deps
├── DEVELOPMENT.md              # Setup guide
├── WORKFLOW_OPTIMIZATION_SUMMARY.md  # Changes overview
├── README.md                   # Project readme
└── build_configs/              # Your code here
```

## Troubleshooting

### Virtual environment not activated
```bash
source .venv/bin/activate
which python  # Should point to .venv/bin/python
```

### Dependencies not installing
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Pre-commit hooks failing
```bash
pre-commit clean
pre-commit install
make format  # Fix formatting first
```

### CI workflow failing
- Check GitHub Actions tab
- Download artifacts for detailed reports
- Run `make check` locally first

## Quick Tips

💡 **Always activate venv**: `source .venv/bin/activate`  
💡 **Format before commit**: `make format`  
💡 **Run checks locally**: `make check` (faster than waiting for CI)  
💡 **Use pre-commit**: Catches issues before commit  
💡 **Read the docs**: See DEVELOPMENT.md for details  

## Help & Resources

- **Setup Issues**: See DEVELOPMENT.md
- **Workflow Details**: See WORKFLOW_OPTIMIZATION_SUMMARY.md  
- **All Commands**: Run `make help`
- **CI Status**: Check GitHub Actions tab

## Version Requirements

- Python: 3.11+ (3.12 recommended)
- Git: 2.30+
- Make: Any recent version

---

**Pro Tip**: Bookmark this file! 🔖
