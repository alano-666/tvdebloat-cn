"""输出：人类可读表格与 JSON。"""
from __future__ import annotations

import json

from .models import Plan, PackageEntry


def plan_to_json(plan: Plan) -> str:
    return json.dumps(plan.to_dict(), ensure_ascii=False, indent=2)


def render_plan(plan: Plan) -> str:
    lines = [
        f"设备: {plan.device}  品牌: {plan.brand}  生成时间: {plan.generated_at}",
        "",
    ]
    if plan.actions:
        lines.append(f"将执行 {len(plan.actions)} 个操作:")
        lines.append(f"{'包名':<45} {'操作':<11} {'风险':<8} 名称")
        lines.append("-" * 100)
        for a in plan.actions:
            lines.append(f"{a.package:<45} {a.kind:<11} {a.risk:<8} {a.name}")
    else:
        lines.append("没有需要执行的操作。")
    if plan.skipped:
        lines.append("")
        lines.append(f"跳过 {len(plan.skipped)} 项:")
        for s in plan.skipped:
            reason = {
                "not_found": "设备上未找到",
                "whitelisted": "在白名单中",
                "high_risk": "高风险(需 --include-high-risk)",
                "low_confidence": "低置信度",
                "keep": "仅信息(推荐保留)",
            }.get(s.reason, s.reason)
            lines.append(f"  - {s.package:<45} {reason}  {s.name}")
    return "\n".join(lines)


def render_entry_list(entries: list[PackageEntry]) -> str:
    if not entries:
        return "（无匹配条目）"
    lines = [
        f"{'包名':<45} {'分类':<11} {'风险':<8} {'置信度':<6} {'建议':<10} 名称"
    ]
    lines.append("-" * 110)
    for e in entries:
        lines.append(
            f"{e.package:<45} {e.category:<11} {e.risk:<8} "
            f"{e.confidence:<6} {e.recommended:<10} {e.name}"
        )
    return "\n".join(lines)


def entries_to_json(entries: list[PackageEntry]) -> str:
    return json.dumps([e.to_dict() for e in entries], ensure_ascii=False, indent=2)
