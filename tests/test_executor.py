"""执行器测试：apply 保存历史，restore 反向回滚。"""
from __future__ import annotations

import json

import pytest

from tvdebloat.device import FakeDevice
from tvdebloat.executor import apply_plan, history_dir, restore_from_history
from tvdebloat.packages import PackageDB
from tvdebloat.planner import build_plan

AD = "com.xiaomi.mitv.advertise"
MIUI_AD = "com.miui.systemAdSolution"


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    monkeypatch.setenv("TVDEBLOAT_HOME", str(tmp_path))
    return tmp_path


def _make_plan(uninstall: bool = False):
    db = PackageDB()
    device = FakeDevice(packages=[AD, MIUI_AD])
    return build_plan(db, device, ["xiaomi"], force_uninstall=uninstall)


def test_apply_requires_yes(fake_home) -> None:
    plan = _make_plan()
    with pytest.raises(RuntimeError, match="--yes"):
        apply_plan(plan, FakeDevice())


def test_apply_executes_and_saves_history(fake_home) -> None:
    plan = _make_plan()
    device = FakeDevice()
    path = apply_plan(plan, device, yes=True)

    assert device.commands == [
        ["shell", "pm", "disable-user", "--user", "0", AD],
        ["shell", "pm", "disable-user", "--user", "0", MIUI_AD],
    ]
    assert path.parent == history_dir()
    assert path.exists()

    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["plan"]["actions"][0]["package"] == AD
    assert state["device"] == device.serial


def test_apply_empty_plan_raises(fake_home) -> None:
    plan = _make_plan()
    plan.actions = []
    with pytest.raises(RuntimeError, match="计划为空"):
        apply_plan(plan, FakeDevice(), yes=True)


def test_restore_reverses_in_order(fake_home) -> None:
    plan = _make_plan(uninstall=True)
    device = FakeDevice()
    path = apply_plan(plan, device, yes=True)

    device2 = FakeDevice()
    count = restore_from_history(path, device2, yes=True)
    assert count == 2
    # 反向顺序执行 revert
    assert device2.commands == [
        ["shell", "cmd", "package", "install-existing", MIUI_AD],
        ["shell", "cmd", "package", "install-existing", AD],
    ]


def test_restore_disable_uses_enable(fake_home) -> None:
    plan = _make_plan()
    device = FakeDevice()
    path = apply_plan(plan, device, yes=True)

    device2 = FakeDevice()
    restore_from_history(path, device2, yes=True)
    assert device2.commands == [
        ["shell", "pm", "enable", MIUI_AD],
        ["shell", "pm", "enable", AD],
    ]


def test_restore_requires_yes(fake_home) -> None:
    plan = _make_plan()
    device = FakeDevice()
    path = apply_plan(plan, device, yes=True)
    with pytest.raises(RuntimeError, match="--yes"):
        restore_from_history(path, FakeDevice())
