from __future__ import annotations

import asyncio
from typing import Optional


class SCPIClient:
    def __init__(self, host: str, port: int = 5025):
        self.host = host
        self.port = port
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    async def _ensure_connected(self):
        if self._writer is not None and not self._writer.is_closing():
            return
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=5.0
        )

    async def send(self, command: str) -> None:
        await self._ensure_connected()
        assert self._writer is not None
        self._writer.write((command + "\n").encode())
        await self._writer.drain()
        await asyncio.sleep(0.05)

    async def query(self, command: str, timeout: float = 5.0) -> str:
        await self._ensure_connected()
        assert self._writer is not None and self._reader is not None
        self._writer.write((command + "\n").encode())
        await self._writer.drain()
        data = await asyncio.wait_for(self._reader.readline(), timeout=timeout)
        return data.decode().strip()

    async def query_binary(self, command: str, timeout: float = 30.0) -> bytes:
        await self._ensure_connected()
        assert self._writer is not None and self._reader is not None
        self._writer.write((command + "\n").encode())
        await self._writer.drain()
        header_start = await asyncio.wait_for(self._reader.readexactly(2), timeout=timeout)
        if header_start[0:1] != b"#":
            rest = await self._reader.readline()
            return header_start + rest
        digit_count = int(header_start[1:2].decode())
        length_bytes = await self._reader.readexactly(digit_count)
        data_length = int(length_bytes.decode())
        data = await self._reader.readexactly(data_length)
        return data

    async def query_raw(
        self,
        command: str,
        idle_timeout: float = 0.5,
        overall_timeout: float = 30.0,
    ) -> bytes:
        """Send a command and read raw binary until the instrument goes idle.

        Used for responses with no IEEE 488.2 length header and no line
        terminator (e.g. the SDS1202X-E ``SCDP`` screenshot, which streams a
        raw PNG/BMP). Reads chunks until ``idle_timeout`` elapses with no new
        data, or ``overall_timeout`` is exceeded.
        """
        await self._ensure_connected()
        assert self._writer is not None and self._reader is not None
        self._writer.write((command + "\n").encode())
        await self._writer.drain()

        loop = asyncio.get_event_loop()
        deadline = loop.time() + overall_timeout
        buf = bytearray()
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            try:
                chunk = await asyncio.wait_for(
                    self._reader.read(65536),
                    timeout=min(idle_timeout, remaining),
                )
            except asyncio.TimeoutError:
                break  # no more data within idle window -> transfer complete
            if not chunk:
                break  # EOF
            buf += chunk
        return bytes(buf)

    def disconnect(self):
        if self._writer and not self._writer.is_closing():
            self._writer.close()
        self._writer = None
        self._reader = None
