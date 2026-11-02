"""数据模型：包条目、执行计划、跳过条目。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

CATEGORIES = {"ad", "preinstall", "ota", "system"}
RISKS = {"low", "medium", "high"}
RECOMMENDED = {"disable", "uninstall", "keep"}
CONFIDENCE = {"low", "medium", "high"}
SKIP_REASONS = {"not_found", "whitelisted", "high_risk", "low_confidence", "keep"}


@dataclass(frozen=True)
class PackageEntry:
    """包名数据库中的一条记录。"""

    package: str
    name: str
    category: str
    risk: str
    recommended: str
    confidence: str
    note: str = ""
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "name": self.name,
            "category": self.category,
            "risk": self.risk,
            "recommended": self.recommended,
            "confidence": self.confidence,
            "note": self.note,
            "source": self.source,
        }


@dataclass(frozen=True)
class PlanAction:
    """计划中的一个操作。kind: disable | uninstall。"""

    package: str
    name: str
    kind: str
    risk: str
    note: str = ""

    def command(self) -> list[str]:
        if self.kind == "uninstall":
            return ["shell", "pm", "uninstall", "--user", "0", self.package]
        return ["shell", "pm", "disable-user", "--user", "0", self.package]

    def revert_command(self) -> list[str]:
        if self.kind == "uninstall":
            return ["shell", "cmd", "package", "install-existing", self.package]
        return ["shell", "pm", "enable", self.package]

    def to_dict(self) -> dict:
        return {
            "package": self.package,
            "name": self.name,
            "kind": self.kind,
            "risk": self.risk,
            "note": self.note,
        }


@dataclass(frozen=True)
class SkippedEntry:
    package: str
    name: str
    reason: str

    def to_dict(self) -> dict:
        return {"package": self.package, "name": self.name, "reason": self.reason}


@dataclass
class Plan:
    brand: str
    device: str
    actions: list[PlanAction] = field(default_factory=list)
    skipped: list[SkippedEntry] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "brand": self.brand,
            "device": self.device,
            "generated_at": self.generated_at,
            "actions": [a.to_dict() for a in self.actions],
            "skipped": [s.to_dict() for s in self.skipped],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        return cls(
            brand=data["brand"],
            device=data["device"],
            generated_at=data.get("generated_at", ""),
            actions=[PlanAction(**a) for a in data.get("actions", [])],
            skipped=[SkippedEntry(**s) for s in data.get("skipped", [])],
        )
