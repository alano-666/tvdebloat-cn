"""包名数据库测试：加载、查询、schema 完整性。"""
from __future__ import annotations

import re

import pytest

from tvdebloat.models import CATEGORIES, CONFIDENCE, RECOMMENDED, RISKS
from tvdebloat.packages import PackageDB

_PKG_RE = re.compile(r"^[a-zA-Z][\w.]*$")


@pytest.fixture(scope="module")
def db() -> PackageDB:
    return PackageDB()


def test_brands_loaded(db: PackageDB) -> None:
    assert "xiaomi" in db.brands
    assert "dangbei" in db.brands


def test_all_entries_pass_schema(db: PackageDB) -> None:
    for brand in db.brands:
        entries = db.query([brand], min_confidence="low")
        assert entries, f"品牌 {brand} 没有条目"
        for e in entries:
            assert _PKG_RE.match(e.package), f"非法包名: {e.package}"
            assert e.name, f"{e.package} 缺少名称"
            assert e.category in CATEGORIES, f"{e.package} 分类非法: {e.category}"
            assert e.risk in RISKS
            assert e.recommended in RECOMMENDED
            assert e.confidence in CONFIDENCE


def test_min_confidence_filters(db: PackageDB) -> None:
    high = db.query(["xiaomi"], min_confidence="high")
    medium = db.query(["xiaomi"], min_confidence="medium")
    low = db.query(["xiaomi"], min_confidence="low")
    assert all(e.confidence == "high" for e in high)
    assert len(high) <= len(medium) <= len(low)


def test_xiaomi_contains_core_ad_packages(db: PackageDB) -> None:
    pkgs = {e.package for e in db.query(["xiaomi"], min_confidence="medium")}
    assert "com.xiaomi.mitv.advertise" in pkgs
    assert "com.miui.systemAdSolution" in pkgs


def test_dedupe_across_brands(db: PackageDB) -> None:
    entries = db.query(["xiaomi", "dangbei"], min_confidence="low")
    pkgs = [e.package for e in entries]
    assert len(pkgs) == len(set(pkgs)), "跨品牌条目应按包名去重"


def test_unknown_brand_raises_with_hint(db: PackageDB) -> None:
    with pytest.raises(KeyError, match="xiaomi"):
        db.query(["not-a-brand"])


def test_invalid_confidence_raises(db: PackageDB) -> None:
    with pytest.raises(ValueError, match="置信度"):
        db.query(["xiaomi"], min_confidence="ultra")


def test_custom_data_dir(tmp_path) -> None:
    (tmp_path / "testbrand.json").write_text(
        '{"name": "测试品牌", "packages": [{"package": "com.test.ad", '
        '"name": "测试广告", "category": "ad", "risk": "low", '
        '"recommended": "disable", "confidence": "high"}]}',
        encoding="utf-8",
    )
    db = PackageDB(data_dir=tmp_path)
    assert db.brands == ["testbrand"]
    assert db.query(["testbrand"])[0].package == "com.test.ad"
