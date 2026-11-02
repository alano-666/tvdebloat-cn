"""CLI 端到端测试：注入 FakeDevice 工厂，验证完整工作流。"""
from __future__ import annotations

import json

import pytest

from tvdebloat.cli import main
from tvdebloat.device import FakeDevice

AD = "com.xiaomi.mitv.advertise"


@pytest.fixture
def factory():
    def make(serial: str) -> FakeDevice:
        return FakeDevice(packages=[AD, "com.miui.systemAdSolution"], serial=serial)

    return make


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    monkeypatch.setenv("TVDEBLOAT_HOME", str(tmp_path))
    return tmp_path


def test_list_shows_brands(factory, capsys) -> None:
    assert main(["list"], device_factory=factory) == 0
    out = capsys.readouterr().out
    assert "com.xiaomi.mitv.advertise" in out
    assert "开机广告服务" in out


def test_list_json(factory, capsys) -> None:
    assert main(["list", "--brand", "xiaomi", "--json"], device_factory=factory) == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert any(e["package"] == AD for e in data)


def test_plan_json(factory, capsys) -> None:
    assert (
        main(
            ["plan", "--device", "fake", "--brand", "xiaomi", "--json"],
            device_factory=factory,
        )
        == 0
    )
    data = json.loads(capsys.readouterr().out)
    assert data["device"] == "fake"
    assert any(a["package"] == AD and a["kind"] == "disable" for a in data["actions"])


def test_plan_human_output_mentions_dry_run_safety(factory, capsys) -> None:
    main(["plan", "--device", "fake", "--brand", "xiaomi"], device_factory=factory)
    out = capsys.readouterr().out
    assert "disable" in out
    assert "设备上未找到" in out  # 未安装的包被跳过并说明


def test_plan_unknown_brand_fails(factory, capsys) -> None:
    assert (
        main(
            ["plan", "--device", "fake", "--brand", "nope"],
            device_factory=factory,
        )
        == 1
    )
    err = capsys.readouterr().err
    assert "未知品牌" in err


def test_full_apply_restore_workflow(factory, fake_home, tmp_path, capsys) -> None:
    plan_file = tmp_path / "plan.json"
    assert (
        main(
            ["plan", "--device", "fake", "--brand", "xiaomi", "--out", str(plan_file)],
            device_factory=factory,
        )
        == 0
    )
    assert plan_file.exists()

    assert (
        main(
            ["apply", "--plan", str(plan_file), "--device", "fake"],
            device_factory=factory,
        )
        == 1
    )
    assert "yes" in capsys.readouterr().err

    assert (
        main(
            ["apply", "--plan", str(plan_file), "--device", "fake", "--yes"],
            device_factory=factory,
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "历史记录" in out
    history = json.loads(plan_file.read_text(encoding="utf-8"))
    history_files = list((fake_home / "history").glob("*.json"))
    assert len(history_files) == 1

    assert (
        main(
            [
                "restore",
                "--history",
                str(history_files[0]),
                "--device",
                "fake",
                "--yes",
            ],
            device_factory=factory,
        )
        == 0
    )
    assert "已回滚" in capsys.readouterr().out


def test_export_json(factory, capsys) -> None:
    assert main(["export"], device_factory=factory) == 0
    data = json.loads(capsys.readouterr().out)
    assert any(e["package"] == AD for e in data)


def test_version(factory, capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"], device_factory=factory)
    assert exc.value.code == 0
    assert "tvdebloat" in capsys.readouterr().out


def test_whitelist_flag(factory, capsys) -> None:
    assert (
        main(
            [
                "plan",
                "--device",
                "fake",
                "--brand",
                "xiaomi",
                "--whitelist",
                AD,
                "--json",
            ],
            device_factory=factory,
        )
        == 0
    )
    data = json.loads(capsys.readouterr().out)
    assert all(a["package"] != AD for a in data["actions"])
    assert any(s["package"] == AD and s["reason"] == "whitelisted" for s in data["skipped"])
