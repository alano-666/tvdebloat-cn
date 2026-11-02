"""计划引擎测试：包名库 × 设备包列表 → 计划。"""
from __future__ import annotations

from tvdebloat.device import FakeDevice
from tvdebloat.packages import PackageDB
from tvdebloat.planner import build_plan

AD = "com.xiaomi.mitv.advertise"
MIUI_AD = "com.miui.systemAdSolution"
TVHOME = "com.mitv.tvhome"
OTA = "com.xiaomi.mitv.upgrade"
APPSTORE = "com.xiaomi.mitv.appstore"

DEVICE_PACKAGES = [AD, MIUI_AD, TVHOME, "com.keepme.installed"]


def _plan(**kwargs) -> dict:
    db = PackageDB()
    device = FakeDevice(packages=DEVICE_PACKAGES)
    plan = build_plan(db, device, ["xiaomi"], **kwargs)
    return {
        "plan": plan,
        "actions": {a.package: a for a in plan.actions},
        "skipped": {s.package: s.reason for s in plan.skipped},
        "device": device,
    }


def test_default_plan_disables_present_ad_packages() -> None:
    r = _plan()
    assert AD in r["actions"] and r["actions"][AD].kind == "disable"
    assert MIUI_AD in r["actions"] and r["actions"][MIUI_AD].kind == "disable"


def test_not_found_skipped() -> None:
    r = _plan()
    assert OTA not in r["actions"]
    assert r["skipped"][OTA] == "not_found"


def test_keep_entries_skipped() -> None:
    r = _plan()
    assert APPSTORE not in r["actions"]
    assert r["skipped"][APPSTORE] == "keep"


def test_high_risk_excluded_by_default() -> None:
    r = _plan()
    assert TVHOME not in r["actions"]
    assert r["skipped"][TVHOME] == "high_risk"


def test_include_high_risk() -> None:
    r = _plan(include_high_risk=True)
    assert TVHOME in r["actions"]
    assert r["actions"][TVHOME].kind == "disable"


def test_whitelist_respected() -> None:
    r = _plan(whitelist={AD})
    assert AD not in r["actions"]
    assert r["skipped"][AD] == "whitelisted"
    assert MIUI_AD in r["actions"]


def test_force_uninstall() -> None:
    r = _plan(force_uninstall=True)
    assert r["actions"][AD].kind == "uninstall"
    assert r["actions"][MIUI_AD].kind == "uninstall"


def test_min_confidence_excludes_low() -> None:
    r = _plan(min_confidence="high")
    # com.xiaomi.ab 是 medium，不应出现在 high 计划中
    assert "com.xiaomi.ab" not in r["actions"]
    assert "com.xiaomi.ab" not in r["skipped"]


def test_commands_are_reversible() -> None:
    r = _plan()
    disable = r["actions"][AD]
    assert disable.command() == ["shell", "pm", "disable-user", "--user", "0", AD]
    assert disable.revert_command() == ["shell", "pm", "enable", AD]
    uninstall = _plan(force_uninstall=True)["actions"][AD]
    assert uninstall.revert_command() == [
        "shell",
        "cmd",
        "package",
        "install-existing",
        AD,
    ]


def test_plan_round_trip() -> None:
    from tvdebloat.models import Plan

    r = _plan()
    restored = Plan.from_dict(r["plan"].to_dict())
    assert restored.brand == r["plan"].brand
    assert restored.device == r["plan"].device
    assert [a.package for a in restored.actions] == [
        a.package for a in r["plan"].actions
    ]
    assert restored.skipped == r["plan"].skipped
