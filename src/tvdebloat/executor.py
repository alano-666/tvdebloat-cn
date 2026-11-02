"""执行器：应用计划并记录历史，支持回滚。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .device import Device
from .models import Plan


def history_dir() -> Path:
    base = Path(os.environ.get("TVDEBLOAT_HOME", Path.home() / ".tvdebloat"))
    return base / "history"


def apply_plan(plan: Plan, device: Device, *, yes: bool = False) -> Path:
    if not plan.actions:
        raise RuntimeError("计划为空，无需执行")
    if not yes:
        raise RuntimeError("未确认执行：apply 需要 --yes 参数")
    for action in plan.actions:
        device.run(action.command())

    state = {
        "plan": plan.to_dict(),
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "device": device.serial,
    }
    hist = history_dir()
    hist.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = hist / f"{ts}-{plan.brand}.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def restore_from_history(path: Path, device: Device, *, yes: bool = False) -> int:
    raw = json.loads(path.read_text(encoding="utf-8"))
    plan = Plan.from_dict(raw["plan"])
    if not yes:
        raise RuntimeError("未确认执行：restore 需要 --yes 参数")
    for action in reversed(plan.actions):
        device.run(action.revert_command())
    return len(plan.actions)
