"""包名数据库：加载 data/brands/*.json，按品牌/置信度查询。

数据库为社区共建：每个品牌一个 JSON 文件，字段与 schema 见 data/README 约定，
贡献方式见仓库 CONTRIBUTING 与 PLAN.md。
"""
from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from .models import PackageEntry

DEFAULT_MIN_CONFIDENCE = "medium"
_CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}


class PackageDB:
    def __init__(self, data_dir: Path | None = None) -> None:
        if data_dir is None:
            data_dir = Path(str(files("tvdebloat").joinpath("data", "brands")))
        self._entries: dict[str, list[PackageEntry]] = {}
        self._meta: dict[str, dict] = {}
        for path in sorted(data_dir.glob("*.json")):
            brand = path.stem
            raw = json.loads(path.read_text(encoding="utf-8"))
            self._meta[brand] = {k: raw[k] for k in ("name", "adb_note") if k in raw}
            self._entries[brand] = [PackageEntry(**item) for item in raw["packages"]]

    @property
    def brands(self) -> list[str]:
        return list(self._entries)

    def brand_info(self, brand: str) -> dict:
        if brand not in self._entries:
            raise KeyError(self._unknown_brand_message(brand))
        info = dict(self._meta.get(brand, {}))
        info["count"] = len(self._entries[brand])
        return info

    def query(
        self,
        brands: list[str],
        *,
        min_confidence: str = DEFAULT_MIN_CONFIDENCE,
        categories: set[str] | None = None,
    ) -> list[PackageEntry]:
        if min_confidence not in _CONFIDENCE_ORDER:
            raise ValueError(f"无效置信度: {min_confidence}，可选: low/medium/high")
        for brand in brands:
            if brand not in self._entries:
                raise KeyError(self._unknown_brand_message(brand))
        min_level = _CONFIDENCE_ORDER[min_confidence]
        deduped: dict[str, PackageEntry] = {}
        for brand in brands:
            for entry in self._entries[brand]:
                if _CONFIDENCE_ORDER[entry.confidence] < min_level:
                    continue
                if categories is not None and entry.category not in categories:
                    continue
                deduped.setdefault(entry.package, entry)
        return list(deduped.values())

    def _unknown_brand_message(self, brand: str) -> str:
        return f"未知品牌: {brand}，可用品牌: {', '.join(self.brands)}"
