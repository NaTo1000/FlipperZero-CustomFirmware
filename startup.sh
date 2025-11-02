#!/bin/bash
# Startup script for FlipperZero Custom Firmware Development
# This script sets up the development environment

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  FlipperZero Custom Firmware - Setup Script${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.8+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if Git is installed
print_info "Checking Git installation..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    print_success "Git $GIT_VERSION found"
else
    print_error "Git not found. Please install Git"
    exit 1
fi

# Create virtual environment if it doesn't exist
print_info "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install requirements
print_info "Installing Python dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed successfully"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Check for unleashed-firmware
print_info "Checking for unleashed-firmware repository..."
if [ -d "../unleashed-firmware" ]; then
    print_success "unleashed-firmware repository found"
else
    print_warning "unleashed-firmware repository not found"
    echo ""
    print_info "To complete the setup, clone the unleashed-firmware repository:"
    echo -e "${YELLOW}  git clone https://github.com/DarkFlippers/unleashed-firmware.git ../unleashed-firmware${NC}"
    echo -e "${YELLOW}  cd ../unleashed-firmware${NC}"
    echo -e "${YELLOW}  git submodule update --init --recursive${NC}"
fi

# Display setup information
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "Virtual environment activated. To deactivate, run: ${BLUE}deactivate${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Clone unleashed-firmware (if not already done)"
echo -e "  2. Copy custom applications to unleashed-firmware:"
echo -e "     ${BLUE}cp -r applications_user/* ../unleashed-firmware/applications_user/${NC}"
echo -e "  3. Copy build configuration:"
echo -e "     ${BLUE}cp build_configs/fbt_options.py ../unleashed-firmware/${NC}"
echo -e "  4. Build firmware:"
echo -e "     ${BLUE}cd ../unleashed-firmware && ./fbt${NC}"
echo ""
print_success "Development environment is ready!"
