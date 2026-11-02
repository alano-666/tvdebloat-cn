# tvdebloat-cn 开发计划

> 基于《GitHub 热门项目分析（2026-11-02）》选型：国产电视去广告工具箱。
> 流量公式：**情绪痛点 × 零门槛 × 可视化 Demo × (AI 生态红利 ∪ 中文社区错位)**。

## Phase 0 — 核心引擎（2026-11-02 ✅ 已完成）

- [x] 项目骨架：src 布局 + pyproject + MIT
- [x] 包名数据库：JSON 数据驱动，小米（8 条）+ 当贝（1 条），含风险/置信度标注
- [x] 计划引擎：dry-run 计划生成，白名单/高风险排除/未找到自动跳过
- [x] 执行器：apply 保存历史、restore 反向回滚
- [x] CLI：list / scan / plan / apply / restore / export，全流程 --json
- [x] 测试：19 个单测覆盖数据库 schema、计划策略、执行/回滚、CLI 端到端
- [x] 发布 GitHub：alano-666/tvdebloat-cn

## Phase 1 — 真机验证 + 数据扩充

- [ ] 真机验证：小米/红米电视实测 scan→plan→apply→restore 全流程，修复 adb 兼容问题
- [ ] 品牌数据扩充：海信、创维、TCL、雷鸟、长虹、乐视（社区 PR 模板 + CONTRIBUTING）
- [ ] `scan` 局域网扫描：自动发现 5555 端口 adb 服务（TCP 扫描 + adb connect）
- [ ] 各品牌 adb 开启方法文档（docs/brands/）
- [ ] GitHub Actions：pytest CI + ruff 静态检查

## Phase 2 — 体验层

- [ ] HTML 清理报告：plan 生成可视化报告（可直接发图传播）
- [ ] 前后对比素材：开机广告 before/after 截图模板，引导用户产出传播素材
- [ ] 一键脚本：`curl | bash` 式安装 + 交互式引导（面向非开发者）
- [ ] 中文文档站（GitHub Pages）

## Phase 3 — Agent 集成 + 传播

- [ ] Claude Code skill：`/tv-clean` 让 AI 智能体完成「连接→计划→执行→回滚」全流程
- [ ] MCP server：结构化工具供任意 agent 调用
- [ ] 传播物料：B站/知乎/小红书对比视频与图文（国产电视开机广告消失实录）
- [ ] Release 发布：PyPI 包 + 二进制（pyinstaller）
- [ ] 数据贡献激励：README 贡献者列表 + 品牌覆盖进度条

## 成功指标

- 首月 500★（对标 android-ad-cleaner 首月 ~6k 的十分之一，保守目标）
- 社区 PR ≥ 5 个品牌数据
- 知乎/B站 至少 1 篇 10w+ 传播内容

## 风险与对策

| 风险 | 对策 |
|---|---|
| 部分品牌 adb 受限（华为智慧屏等） | 数据库标注 adb 可用性，聚焦可 adb 品牌 |
| 真机不可得 | 先以社区数据 + 文档驱动，向社区征集验证报告 |
| 与 cleanyourtv 同质化 | 差异化：国产品牌数据 + 安全设计 + agent 集成 |
| 系统更新导致包名变化 | 数据版本化 + 设备包列表自动匹配（未找到自动跳过） |
