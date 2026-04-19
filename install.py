#!/usr/bin/env python3
"""
install.py — Cross-platform installer for FlipperZero CustomFirmware
=====================================================================
Works on Windows, macOS, and Linux (anywhere Python 3.8+ is installed).

Usage:
    python install.py [--no-venv] [--skip-firmware] [--dfu]

Options:
    --no-venv        Skip Python virtual-environment creation
    --skip-firmware  Only set up the Python env, don't clone/build firmware
    --dfu            Print DFU recovery instructions and exit
    --help           Show this help message
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# ── Colour helpers (ANSI – disabled on Windows unless colorama is available) ──

def _supports_colour() -> bool:
    if platform.system() == "Windows":
        try:
            import colorama  # type: ignore
            colorama.init()
            return True
        except ImportError:
            return False
    return True


USE_COLOUR = _supports_colour()

def _c(code: str, text: str) -> str:
    if not USE_COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"

def info(msg: str)    -> None: print(_c("34", "[INFO]   ") + msg)
def ok(msg: str)      -> None: print(_c("32", "[OK]     ") + msg)
def warn(msg: str)    -> None: print(_c("33", "[WARN]   ") + msg)
def error(msg: str)   -> None: print(_c("31", "[ERROR]  ") + msg)
def header(msg: str)  -> None: print(_c("34;1", "=" * 54)); print(_c("34;1", f"  {msg}")); print(_c("34;1", "=" * 54))


# ── Subprocess helpers ────────────────────────────────────────

def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> int:
    info(f"Running: {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        error(f"Command failed (exit {result.returncode}): {' '.join(str(c) for c in cmd)}")
        sys.exit(result.returncode)
    return result.returncode


def which(name: str) -> str | None:
    return shutil.which(name)


# ── Checks ────────────────────────────────────────────────────

def check_python() -> None:
    info("Checking Python version...")
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        error(f"Python 3.8+ required; found {major}.{minor}")
        sys.exit(1)
    ok(f"Python {major}.{minor} found")


def check_git() -> None:
    info("Checking Git...")
    if not which("git"):
        error("Git not found.  Install it from https://git-scm.com/")
        sys.exit(1)
    result = subprocess.run(["git", "--version"], capture_output=True, text=True)
    ok(result.stdout.strip())


def check_dfu_util() -> None:
    info("Checking dfu-util...")
    if which("dfu-util"):
        ok("dfu-util found")
    else:
        warn("dfu-util not found — needed for DFU flashing.")
        _print_dfu_install_hint()


def _print_dfu_install_hint() -> None:
    sys_name = platform.system()
    if sys_name == "Darwin":
        print("  Install with:  brew install dfu-util")
    elif sys_name == "Linux":
        print("  Install with:  sudo apt install dfu-util   (Debian/Ubuntu)")
        print("              or sudo dnf install dfu-util   (Fedora)")
    else:
        print("  Download from: https://dfu-util.sourceforge.net/")


# ── Virtual environment ───────────────────────────────────────

def setup_venv(root: Path) -> Path:
    venv_dir = root / ".venv"
    info("Setting up Python virtual environment...")
    if not venv_dir.exists():
        run([sys.executable, "-m", "venv", str(venv_dir)])
        ok("Virtual environment created")
    else:
        info("Virtual environment already exists")

    return venv_dir


def get_pip(venv_dir: Path) -> str:
    """Return the path to pip inside the venv."""
    if platform.system() == "Windows":
        return str(venv_dir / "Scripts" / "pip.exe")
    return str(venv_dir / "bin" / "pip")


def install_requirements(root: Path, pip: str) -> None:
    req = root / "requirements.txt"
    if not req.exists():
        warn("requirements.txt not found — skipping pip install")
        return
    info("Installing Python dependencies...")
    run([pip, "install", "--upgrade", "pip", "--quiet"])
    run([pip, "install", "-r", str(req)])
    ok("Python dependencies installed")


# ── Firmware setup ────────────────────────────────────────────

def setup_firmware(root: Path) -> None:
    fw_dir = root.parent / "unleashed-firmware"
    info(f"Checking for unleashed-firmware at {fw_dir} ...")

    if not fw_dir.exists():
        info("Cloning unleashed-firmware (this may take several minutes)...")
        run(
            ["git", "clone",
             "https://github.com/DarkFlippers/unleashed-firmware.git",
             str(fw_dir)],
        )
        info("Initialising submodules (this may take 10-30 minutes)...")
        run(["git", "submodule", "update", "--init", "--recursive"], cwd=fw_dir)
        ok("unleashed-firmware cloned and ready")
    else:
        ok("unleashed-firmware directory found")

    # Copy custom apps
    info("Copying custom applications...")
    src_apps = root / "applications_user"
    dst_apps = fw_dir / "applications_user"
    for item in src_apps.iterdir():
        dst = dst_apps / item.name
        if item.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(item, dst)
    ok("Custom applications copied")

    # Copy build config
    info("Copying build configuration...")
    shutil.copy(root / "build_configs" / "fbt_options.py", fw_dir / "fbt_options.py")
    ok("fbt_options.py copied")


# ── DFU instructions ──────────────────────────────────────────

DFU_INSTRUCTIONS = """
╔══════════════════════════════════════════════════════╗
║              Flipper Zero — DFU Flashing             ║
╚══════════════════════════════════════════════════════╝

Method A — Flash via FBT (recommended)
───────────────────────────────────────
  1. Connect Flipper Zero via USB
  2. cd unleashed-firmware
  3. ./fbt flash_usb          (Linux / macOS)
     python fbt flash_usb     (Windows)

Method B — DFU Recovery (device bricked / won't boot)
───────────────────────────────────────────────────────
  1. Hold the LEFT navigation button
  2. While holding LEFT, plug in the USB cable
     → The device enters DFU mode (screen stays dark)
  3. Verify DFU mode:
       dfu-util -l
     You should see: "Found DFU: [0483:df11]"
  4. Flash the .dfu file:
       dfu-util -d 0483:df11 -a 0 -s 0x08000000 \\
                -D dist/f7-D/flipper-z-full.dfu
  5. Disconnect USB — Flipper reboots normally

Method C — qFlipper GUI (easiest for beginners)
────────────────────────────────────────────────
  1. Install qFlipper: https://flipperzero.one/update
  2. Connect Flipper Zero via USB
  3. Click "Install from file" → select the .dfu from dist/f7-D/
  4. Wait for completion and reboot

DFU file location after build:
  unleashed-firmware/dist/f7-D/flipper-z-full.dfu

Troubleshooting:
  • Linux "permission denied": sudo udevadm trigger
    Add udev rule: SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483",
                   ATTRS{idProduct}=="df11", TAG+="uaccess"
  • Windows: Install STM32 DFU driver via Zadig (https://zadig.akeo.ie/)
  • macOS:   No extra drivers needed; dfu-util via brew works directly
"""


# ── Entry point ───────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="FlipperZero CustomFirmware cross-platform installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--no-venv",        action="store_true", help="Skip venv creation")
    parser.add_argument("--skip-firmware",  action="store_true", help="Skip firmware clone/copy")
    parser.add_argument("--dfu",            action="store_true", help="Show DFU instructions and exit")
    args = parser.parse_args()

    if args.dfu:
        print(DFU_INSTRUCTIONS)
        sys.exit(0)

    header("FlipperZero CustomFirmware Installer")
    print(f"  Platform : {platform.system()} {platform.machine()}")
    print(f"  Python   : {sys.version.split()[0]}")
    print()

    root = Path(__file__).resolve().parent

    check_python()
    check_git()
    check_dfu_util()

    if not args.no_venv:
        venv_dir = setup_venv(root)
        pip = get_pip(venv_dir)
        install_requirements(root, pip)
    else:
        info("Skipping venv creation (--no-venv)")

    if not args.skip_firmware:
        setup_firmware(root)
    else:
        info("Skipping firmware setup (--skip-firmware)")

    print()
    header("Setup Complete!")
    print()
    print("  Next steps:")
    print("  1. cd ../unleashed-firmware")
    if platform.system() == "Windows":
        print("  2. python fbt")
        print("  3. python fbt flash_usb")
    else:
        print("  2. ./fbt")
        print("  3. ./fbt flash_usb")
    print()
    print("  For DFU recovery instructions:")
    print(f"  python {Path(__file__).name} --dfu")
    print()
    ok("Done!")


if __name__ == "__main__":
    main()
