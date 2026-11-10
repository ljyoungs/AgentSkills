# douyin-traffic-psy 🎯

**抖音智能引流助手 V3** — 基于 Chrome DevTools MCP 的半自动化评论引流工具。现有运行说明基于 [WorkBuddy](https://www.codebuddy.cn/workbuddy) 和 Chrome。

> 零快照架构 · 行业预设模板 · 对话配置 · 环境诊断

---

## ✨ 功能亮点

| 功能 | 说明 |
|------|------|
| 🔍 **智能搜索** | 关键词搜索 + 热度排序 + 自动筛选 3 个高潜视频 |
| 💬 **评论扫描** | 批量提取评论 + 多关键词匹配 + 新鲜度过滤（可配置天数） |
| 📊 **可视化报告** | 自动生成 HTML 扫描报告（柱状图 + 饼图 + 匹配列表） |
| 🔁 **模板轮换** | 多条回复模板随机轮换，降低重复率 |
| 🛡️ **风控保护** | 日限额 / 回复间隔 / 验证码检测 / 自动暂停 |
| 🏭 **行业模板** | 7 大行业预设（旅游/教育/电商/本地生活/健身/美妆/知识付费） |
| 🩺 **环境诊断** | `setup_wizard.py check` 一键检测所有依赖 |
| 📦 **配置管理** | 完整 CRUD + 导入导出 + AI 对话式初始化引导 |

---

## 一句话安装

把下面这句话发给能访问 GitHub 并安装技能的 Codex 或 WorkBuddy。

```text
请从 https://github.com/ljyoungs/AgentSkills/tree/main/skills/social-media/douyin-traffic-psy 安装 douyin-traffic-psy-v3 技能，并确认它已能在当前智能体中调用。
```

智能体会获取完整技能包，安装后检查是否可调用。当前抖音运行说明基于 WorkBuddy，Codex 的实际抖音操作尚待验证。

## 运行条件

- 已有运行说明以 WorkBuddy Agent、可用的 Chrome DevTools MCP 连接和 Chrome CDP 为基础。
- 随包 V3 诊断要求 Chrome 144 或更新版本。运行时需要能访问用户已登录抖音的可见标签页；优先复用现有可用的 Chrome 会话及调试连接。登录和验证由用户处理。
- 环境诊断和配置管理工具需要 Python 3。安装技能不等于获得浏览器访问权限，也不会启动扫描或回复。

## 在对话里使用

先在对话里检查环境：

```text
使用 douyin-traffic-psy-v3，检查运行环境，先不扫描、不回复。
```

首次使用时，在对话里说明引流领域、搜索关键词和目标评论。智能体可根据行业预设提出匹配词、回复模板、评论新鲜度和回复上限；你可以修改后确认使用。之后也可以在对话里调整话题、限额和模板。

```text
使用 douyin-traffic-psy-v3 扫描「云南旅游攻略」，列出匹配评论和报告，先不要点击或提交回复。
```

---

## 📁 文件结构

```
douyin-traffic-psy/
├── SKILL.md                    # 技能入口（SOP + 故障排查）
├── config.example.json         # 对话初始化的配置示例
├── .gitignore
├── README.md
│
├── scripts/
│   ├── douyin_tools.js         # 核心：抖音页面 JS 交互函数集
│   ├── config_manager.py       # 配置管理（CRUD / 模板 / 导入导出 / 统计）
│   └── setup_wizard.py         # 环境诊断工具
│
├── assets/                     # 截图 / 演示图
└── docs/
    ├── architecture.md         # 技术架构说明
    └── CHANGELOG.md            # 版本更新记录
```

---

## 🔧 技术架构

- **运行环境**: WorkBuddy Agent + Chrome DevTools Protocol (CDP)
- **页面交互**: `evaluate_script` 注入 JS，零截图低 Token 消耗
- **评论提取**: CSS 选择器 + DOM 遍历，兼容抖音多版 UI
- **状态机**: 搜索 → 排序 → 筛选 → 导航 → 滚动 → 提取 → (回复)

详见 [docs/architecture.md](docs/architecture.md)

---

## ⚠️ 使用须知

- 本工具仅供**学习研究**和**合规营销**目的使用
- 请勿高频刷量，遵守抖音平台服务条款
- 安装、诊断或扫描请求不等于授权回复。只有用户明确要求回复时才操作，遇到验证码或平台限制时暂停。
- 建议每日回复不超过 30 条，避免账号风险
- **作者不对账号封禁等后果负责**

---

## 📋 版本历史

| 版本 | 特性 |
|------|------|
| V3.0 | AI 对话式初始化 + 行业模板 + 一键诊断 + 配置导入导出 |
| V2.0 | 零快照架构 + 多关键词匹配 + 风控保护 |
| V1.0 | 基础搜索 + 评论提取 + 手动回复 |

---

## 📄 License

MIT © [ljyoungs](https://github.com/ljyoungs)
