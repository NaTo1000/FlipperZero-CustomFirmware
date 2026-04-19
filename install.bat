@echo off
REM ============================================================
REM  install.bat — Windows installer for FlipperZero CustomFirmware
REM  Requires Python 3.8+ and Git to be in PATH.
REM ============================================================

SETLOCAL ENABLEEXTENSIONS

SET "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ====================================================
echo   FlipperZero CustomFirmware - Windows Installer
echo ====================================================
echo.

REM ── Check Python ────────────────────────────────────────────
WHERE python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ from https://python.org
    GOTO :EOF
)

FOR /F "tokens=2" %%V IN ('python --version 2^>^&1') DO SET PY_VER=%%V
echo [OK]    Python %PY_VER% found

REM ── Check Git ───────────────────────────────────────────────
WHERE git >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git not found. Please install Git from https://git-scm.com
    GOTO :EOF
)

FOR /F "tokens=3" %%V IN ('git --version 2^>^&1') DO SET GIT_VER=%%V
echo [OK]    Git %GIT_VER% found

REM ── Check dfu-util ──────────────────────────────────────────
WHERE dfu-util >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [WARN]  dfu-util not found. Download from https://dfu-util.sourceforge.net/
    echo         Windows also needs the STM32 DFU driver via Zadig: https://zadig.akeo.ie/
) ELSE (
    echo [OK]    dfu-util found
)

echo.

REM ── Delegate to Python installer ────────────────────────────
echo [INFO]  Running Python installer...
python install.py %*
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Installer failed with exit code %ERRORLEVEL%
    pause
    EXIT /B %ERRORLEVEL%
)

echo.
echo [OK]    Installation complete!
echo.
echo   Next steps:
echo     cd ..\unleashed-firmware
echo     python fbt
echo     python fbt flash_usb
echo.
echo   DFU instructions:
echo     python install.py --dfu
echo.
pause
