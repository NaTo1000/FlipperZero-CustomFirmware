"""
ConductorAgent — direct Flipper Zero device operations.

Wraps WebSerial/pyserial commands for:
  - Firmware flashing
  - File upload/download to SD card
  - Serial console
  - Device info and reboot
  - NFC, Sub-GHz, IR, BadUSB, iButton operations
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Optional


class FlipperCommand(str, Enum):
    INFO = "device_info\r\n"
    REBOOT = "reboot\r\n"
    REBOOT_DFU = "reboot 2\r\n"
    STORAGE_LIST = "storage list /ext\r\n"
    NFC_DETECT = "nfc detect\r\n"
    SUBGHZ_RX = "subghz rx\r\n"
    IR_RX = "ir rx\r\n"


@dataclass
class DeviceResponse:
    command: str
    output: str
    success: bool
    error: Optional[str] = None


class ConductorAgent:
    """
    Sends commands to a connected Flipper Zero.

    In production: wraps pyserial async or the WebSerial bridge.
    In CI/dev: returns stub responses.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baud: int = 230400,
        stub_mode: bool = False,
    ) -> None:
        self._port = port
        self._baud = baud
        self._stub = stub_mode
        self._serial = None

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> bool:
        if self._stub:
            return True
        try:
            import serial_asyncio  # type: ignore
            self._reader, self._writer = await serial_asyncio.open_serial_connection(
                url=self._port, baudrate=self._baud
            )
            return True
        except Exception as exc:
            raise ConnectionError(f"Failed to connect to Flipper on {self._port}: {exc}") from exc

    async def disconnect(self) -> None:
        if self._stub or self._serial is None:
            return
        self._writer.close()
        await self._writer.wait_closed()

    # ------------------------------------------------------------------
    # Device operations
    # ------------------------------------------------------------------

    async def device_info(self) -> DeviceResponse:
        return await self._send(FlipperCommand.INFO)

    async def reboot(self, dfu: bool = False) -> DeviceResponse:
        cmd = FlipperCommand.REBOOT_DFU if dfu else FlipperCommand.REBOOT
        return await self._send(cmd)

    async def list_storage(self) -> DeviceResponse:
        return await self._send(FlipperCommand.STORAGE_LIST)

    async def upload_file(self, local_path: str, remote_path: str) -> DeviceResponse:
        """Upload a file to the Flipper's SD card via storage write."""
        cmd = f"storage write {remote_path}\r\n"
        return await self._send(cmd, description=f"upload {local_path} → {remote_path}")

    async def download_file(self, remote_path: str) -> DeviceResponse:
        """Download a file from the Flipper's SD card."""
        cmd = f"storage read {remote_path}\r\n"
        return await self._send(cmd, description=f"download {remote_path}")

    async def nfc_detect(self) -> DeviceResponse:
        return await self._send(FlipperCommand.NFC_DETECT)

    async def subghz_rx(self) -> DeviceResponse:
        return await self._send(FlipperCommand.SUBGHZ_RX)

    async def ir_rx(self) -> DeviceResponse:
        return await self._send(FlipperCommand.IR_RX)

    async def stream_log(self) -> AsyncGenerator[str, None]:
        """Stream serial output line by line."""
        if self._stub:
            for line in ["[ConductorX] Stub log line 1", "[ConductorX] Stub log line 2"]:
                yield line
                await asyncio.sleep(0.1)
            return
        while True:
            line = await self._reader.readline()
            yield line.decode(errors="replace").rstrip()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _send(
        self, command: FlipperCommand | str, description: str = ""
    ) -> DeviceResponse:
        cmd_str = command.value if isinstance(command, FlipperCommand) else command
        desc = description or cmd_str.strip()

        if self._stub:
            return DeviceResponse(
                command=desc,
                output=f"[STUB] OK: {desc}",
                success=True,
            )
        try:
            self._writer.write(cmd_str.encode())
            await self._writer.drain()
            response = await asyncio.wait_for(self._reader.read(4096), timeout=5.0)
            return DeviceResponse(
                command=desc,
                output=response.decode(errors="replace"),
                success=True,
            )
        except asyncio.TimeoutError:
            return DeviceResponse(command=desc, output="", success=False, error="Timeout")
        except Exception as exc:
            return DeviceResponse(command=desc, output="", success=False, error=str(exc))
