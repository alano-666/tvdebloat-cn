# 📺 tvdebloat-cn · 国产电视去广告工具箱

> **开机广告、桌面广告位、预装全家桶——一台电视而已，凭什么？**
>
> 通过 Wi-Fi 连接 adb，数据驱动生成清理计划。**默认 dry-run，先看计划再动手；只 disable 不卸载，随时可回滚。免 root。**

EN: Debloat Chinese smart TVs (Xiaomi/Redmi and more) over Wi-Fi adb — plan-first, reversible, no root.

## ✨ 特性

- 📶 **Wi-Fi 连接**：无需数据线、无需 root，`tvdebloat scan --host <电视IP>:5555` 即可连接
- 📋 **默认 dry-run**：`plan` 只生成计划不执行，**所有操作执行前你都能看到完整清单**
- 🔄 **只 disable 可回滚**：默认 `pm disable-user`（不用卸载），每次 `apply` 自动保存历史，`restore` 一键还原
- 🛡️ **风险分级**：每条数据标注风险（low/medium/high）与置信度，高风险条目默认排除；设备上不存在的包自动跳过
- 📦 **数据驱动**：包名库是纯 JSON，社区 PR 即可扩充新品牌（海信/创维/TCL/雷鸟…等你来贡献）
- 🤖 **Agent 友好**：全流程支持 `--json` 输出，未来可直接被 Claude Code 等 AI 智能体调用

## 🚀 快速开始

```bash
# 1. 安装（需要 Python 3.10+）
pip install -e .
# 或发布后: pipx install tvdebloat-cn

# 2. 安装 adb（macOS）
brew install --cask android-platform-tools

# 3. 在电视上开启 adb
#    小米电视: 设置 → 关于 → 连点「版本号」→ 开发者选项 → 开启 USB/网络调试

# 4. Wi-Fi 连接电视（电视和电脑同一局域网）
tvdebloat scan --host 192.168.1.10:5555

# 5. 查看清理计划（dry-run，不执行任何操作）
tvdebloat plan --device 192.168.1.10:5555 --brand xiaomi

# 6. 确认无误后执行（自动保存历史）
tvdebloat apply --plan plan.json --device 192.168.1.10:5555 --yes

# 7. 想恢复？一键回滚
tvdebloat restore --history ~/.tvdebloat/history/<时间戳>.json --device 192.168.1.10:5555 --yes
```

常用命令：

```bash
tvdebloat list --brand xiaomi          # 查看数据库条目
tvdebloat list --brand xiaomi --json   # JSON 输出（agent 友好）
tvdebloat export                       # 导出全部数据库
tvdebloat plan ... --whitelist com.xiaomi.mitv.tvmanager   # 保留指定包
tvdebloat plan ... --uninstall         # 改为卸载（仍可 restore 恢复）
```

## 📺 支持品牌

| 品牌 | 状态 | 说明 |
|---|---|---|
| 小米 / 红米电视（MIUI TV） | ✅ 初版收录 | 开机广告、系统广告、预装组件等 8 条（含风险分级） |
| 当贝（多品牌预装） | ✅ 初版收录 | 当贝桌面 |
| 海信 / 创维 / TCL / 雷鸟 / 长虹 | 🚧 待社区贡献 | 见下方「如何贡献数据」 |

> ⚠️ 包名库由社区维护，**执行前请务必核对 plan 输出**。条目带置信度标注；设备上没有的包会自动跳过。

## 🛠️ 工作原理

```
包名数据库(JSON) × 设备实际包列表(pm list packages)
        ↓
   清理计划 plan ── dry-run 展示 + 风险/置信度标注
        ↓ --yes
   pm disable-user --user 0 <pkg>   ← 可逆！pm enable 即可还原
        ↓
   历史记录 → restore 一键回滚
```

- **不 root**：`disable-user --user 0` 是 adb 即可执行的用户级禁用，不修改系统分区
- **不卸载优先**：禁用与卸载效果相同（应用消失且不运行），但禁用恢复更简单
- **历史可审计**：每次 apply 都保存完整 JSON 到 `~/.tvdebloat/history/`

## 🤝 如何贡献数据

1. 在电视上执行 `adb shell pm list packages` 导出包列表
2. 对照确认哪些是广告/预装组件，参考 `src/tvdebloat/data/brands/xiaomi.json` 的格式
3. 提交 PR 新增 `src/tvdebloat/data/brands/<品牌>.json`

字段说明：`package`（包名）、`name`（中文名）、`category`（ad/preinstall/ota/system）、`risk`（low/medium/high）、`recommended`（disable/uninstall/keep）、`confidence`（high/medium/low，不确定就写 low，工具会默认过滤）、`note`（操作说明）、`source`（信息来源）。

## 🗺️ 路线图

见 [PLAN.md](PLAN.md)。当前 Phase 0 已完成核心引擎，下一步：真机验证 + 更多品牌数据。

## ⚠️ 免责声明

本工具仅提供计划与执行能力，**操作前请自行核对每个包的作用**。禁用系统组件可能导致部分功能异常（均已通过风险分级提示）。请勿在重要设备上盲目操作；因使用本工具造成的任何损失，作者不承担责任。

## 📄 License

MIT
