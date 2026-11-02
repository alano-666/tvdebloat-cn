"""命令行入口。

子命令：
  list      列出包名数据库条目
  scan      查看已连接设备 / 通过 Wi-Fi 连接设备
  plan      生成清理计划（默认 dry-run，不执行任何操作）
  apply     执行计划（需 --yes，自动保存历史用于回滚）
  restore   按历史记录回滚（需 --yes）
  export    导出数据库条目为 JSON
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

from . import __version__
from .device import AdbDevice, Device, DeviceError
from .executor import apply_plan, history_dir, restore_from_history
from .models import Plan
from .packages import DEFAULT_MIN_CONFIDENCE, PackageDB
from .planner import build_plan
from .report import (
    entries_to_json,
    plan_to_json,
    render_entry_list,
    render_plan,
)

DeviceFactory = Callable[[str], Device]


def _parse_brands(value: str) -> list[str]:
    return [b.strip() for b in value.split(",") if b.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tvdebloat",
        description="国产智能电视去广告工具箱：Wi-Fi adb 连接，数据驱动清理计划，默认 dry-run，可回滚",
    )
    parser.add_argument("--version", action="version", version=f"tvdebloat {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="列出包名数据库条目")
    p_list.add_argument("--brand", default="", help="品牌，逗号分隔（默认全部）")
    p_list.add_argument(
        "--min-confidence",
        default=DEFAULT_MIN_CONFIDENCE,
        choices=["low", "medium", "high"],
        help="最低置信度（默认 medium）",
    )
    p_list.add_argument("--json", action="store_true", help="JSON 输出")

    p_scan = sub.add_parser("scan", help="查看已连接设备 / Wi-Fi 连接设备")
    p_scan.add_argument("--host", help="通过 Wi-Fi 连接，如 192.168.1.10:5555")

    p_plan = sub.add_parser("plan", help="生成清理计划（dry-run，不执行）")
    p_plan.add_argument("--device", required=True, help="设备序列号或 IP:端口")
    p_plan.add_argument("--brand", required=True, help="品牌，逗号分隔，如 xiaomi")
    p_plan.add_argument("--whitelist", default="", help="保留的包名，逗号分隔")
    p_plan.add_argument(
        "--uninstall", action="store_true", help="disable 改为卸载（仍可用 restore 恢复）"
    )
    p_plan.add_argument(
        "--include-high-risk", action="store_true", help="包含高风险条目（谨慎）"
    )
    p_plan.add_argument(
        "--min-confidence",
        default=DEFAULT_MIN_CONFIDENCE,
        choices=["low", "medium", "high"],
    )
    p_plan.add_argument("--json", action="store_true", help="JSON 输出")
    p_plan.add_argument("--out", help="保存计划到文件（供 apply 使用）")

    p_apply = sub.add_parser("apply", help="执行计划（需 --yes）")
    p_apply.add_argument("--plan", required=True, help="plan --out 保存的计划文件")
    p_apply.add_argument("--device", required=True)
    p_apply.add_argument("--yes", action="store_true", help="确认执行")

    p_restore = sub.add_parser("restore", help="按历史记录回滚（需 --yes）")
    p_restore.add_argument("--history", required=True, help="历史文件路径")
    p_restore.add_argument("--device", required=True)
    p_restore.add_argument("--yes", action="store_true", help="确认执行")

    p_export = sub.add_parser("export", help="导出数据库为 JSON")
    p_export.add_argument("--brand", default="", help="品牌，逗号分隔（默认全部）")
    p_export.add_argument(
        "--min-confidence",
        default=DEFAULT_MIN_CONFIDENCE,
        choices=["low", "medium", "high"],
    )
    return parser


def _default_device_factory(serial: str) -> Device:
    return AdbDevice(serial)


def main(
    argv: list[str] | None = None,
    device_factory: DeviceFactory | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    factory = device_factory or _default_device_factory
    db = PackageDB()

    try:
        if args.command == "list":
            brands = _parse_brands(args.brand) or db.brands
            entries = db.query(brands, min_confidence=args.min_confidence)
            print(entries_to_json(entries) if args.json else render_entry_list(entries))

        elif args.command == "scan":
            if args.host:
                print(AdbDevice.connect(args.host))
            else:
                serials = AdbDevice.connected()
                if serials:
                    print("已连接设备:")
                    for s in serials:
                        print(f"  {s}")
                else:
                    print("没有已连接的设备。用法: tvdebloat scan --host 192.168.x.x:5555")

        elif args.command == "plan":
            device = factory(args.device)
            plan = build_plan(
                db,
                device,
                _parse_brands(args.brand),
                min_confidence=args.min_confidence,
                whitelist=set(_parse_brands(args.whitelist)),
                include_high_risk=args.include_high_risk,
                force_uninstall=args.uninstall,
            )
            output = plan_to_json(plan) if args.json else render_plan(plan)
            if args.out:
                Path(args.out).write_text(
                    json.dumps(plan.to_dict(), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print(f"计划已保存到 {args.out}")
            print(output)

        elif args.command == "apply":
            raw = json.loads(Path(args.plan).read_text(encoding="utf-8"))
            plan = Plan.from_dict(raw)
            history = apply_plan(plan, factory(args.device), yes=args.yes)
            print(f"已执行 {len(plan.actions)} 个操作，历史记录: {history}")
            print(f"回滚: tvdebloat restore --history {history} --device {args.device} --yes")

        elif args.command == "restore":
            count = restore_from_history(
                Path(args.history), factory(args.device), yes=args.yes
            )
            print(f"已回滚 {count} 个操作")

        elif args.command == "export":
            brands = _parse_brands(args.brand) or db.brands
            print(entries_to_json(db.query(brands, min_confidence=args.min_confidence)))

    except (DeviceError, RuntimeError, KeyError, ValueError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
