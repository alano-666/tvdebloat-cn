"""计划引擎：包名库 × 设备实际包列表 → 可审阅的清理计划。

安全策略：
- 默认只生成 disable（可回滚），uninstall 需显式 --uninstall；
- high 风险条目默认排除，需 --include-high-risk；
- 设备上不存在的包自动跳过（not_found），绝不对未确认的包执行操作。
"""
from __future__ import annotations

from .device import Device
from .models import Plan, PlanAction, SkippedEntry
from .packages import PackageDB


def build_plan(
    db: PackageDB,
    device: Device,
    brands: list[str],
    *,
    min_confidence: str = "medium",
    whitelist: set[str] | None = None,
    include_high_risk: bool = False,
    force_uninstall: bool = False,
) -> Plan:
    whitelist = whitelist or set()
    entries = db.query(brands, min_confidence=min_confidence)
    device_packages = set(device.list_packages())

    actions: list[PlanAction] = []
    skipped: list[SkippedEntry] = []
    for entry in entries:
        if entry.package in whitelist:
            skipped.append(SkippedEntry(entry.package, entry.name, "whitelisted"))
            continue
        if entry.recommended == "keep":
            skipped.append(SkippedEntry(entry.package, entry.name, "keep"))
            continue
        if entry.risk == "high" and not include_high_risk:
            skipped.append(SkippedEntry(entry.package, entry.name, "high_risk"))
            continue
        if entry.package not in device_packages:
            skipped.append(SkippedEntry(entry.package, entry.name, "not_found"))
            continue
        kind = (
            "uninstall"
            if force_uninstall or entry.recommended == "uninstall"
            else "disable"
        )
        actions.append(
            PlanAction(
                package=entry.package,
                name=entry.name,
                kind=kind,
                risk=entry.risk,
                note=entry.note,
            )
        )

    return Plan(
        brand=",".join(brands),
        device=device.serial,
        actions=actions,
        skipped=skipped,
    )
