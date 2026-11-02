"""adb 设备抽象：AdbDevice 包装 adb 二进制，FakeDevice 用于测试。"""
from __future__ import annotations

import shutil
import subprocess
from typing import Protocol


class DeviceError(RuntimeError):
    pass


class Device(Protocol):
    serial: str

    def run(self, args: list[str]) -> str: ...

    def list_packages(self) -> list[str]: ...


def find_adb() -> str | None:
    return shutil.which("adb")


def _adb_missing() -> DeviceError:
    return DeviceError(
        "未找到 adb 命令。macOS 安装: brew install --cask android-platform-tools；"
        "其他平台下载 platform-tools 并加入 PATH 后重试"
    )


class AdbDevice:
    """通过 adb 二进制与设备交互。"""

    def __init__(self, serial: str, adb: str | None = None) -> None:
        self.serial = serial
        self.adb = adb or find_adb()
        if not self.adb:
            raise _adb_missing()

    def run(self, args: list[str]) -> str:
        cmd = [self.adb, "-s", self.serial, *args]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired as exc:
            raise DeviceError(f"adb 超时: {' '.join(cmd)}") from exc
        if proc.returncode != 0:
            raise DeviceError(f"adb 失败 ({proc.returncode}): {proc.stderr.strip()}")
        return proc.stdout

    def list_packages(self) -> list[str]:
        out = self.run(["shell", "pm", "list", "packages"])
        return [
            line.removeprefix("package:").strip()
            for line in out.splitlines()
            if line.startswith("package:")
        ]

    @staticmethod
    def connected(adb: str | None = None) -> list[str]:
        adb = adb or find_adb()
        if not adb:
            raise _adb_missing()
        out = subprocess.run(
            [adb, "devices"], capture_output=True, text=True, timeout=15
        ).stdout
        return [
            parts[0]
            for line in out.splitlines()[1:]
            if len(parts := line.split()) == 2 and parts[1] == "device"
        ]

    @staticmethod
    def connect(host: str, adb: str | None = None) -> str:
        adb = adb or find_adb()
        if not adb:
            raise _adb_missing()
        proc = subprocess.run(
            [adb, "connect", host], capture_output=True, text=True, timeout=15
        )
        return (proc.stdout + proc.stderr).strip()


class FakeDevice:
    """测试用设备：返回预置包列表，记录所有已执行命令。"""

    def __init__(self, packages: list[str] | None = None, serial: str = "fake") -> None:
        self.serial = serial
        self._packages = list(packages or [])
        self.commands: list[list[str]] = []

    def run(self, args: list[str]) -> str:
        self.commands.append(list(args))
        return ""

    def list_packages(self) -> list[str]:
        return list(self._packages)
