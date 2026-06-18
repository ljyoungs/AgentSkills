# douyin-traffic-psy 🎯

**抖音智能引流助手 V3** — 基于 Chrome DevTools MCP 的半自动化评论引流工具，运行在 [WorkBuddy](https://www.codebuddy.cn/workbuddy) AI 助手中。

> 零快照架构 · 行业预设模板 · 一键环境诊断 · 开箱即用

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

## 📸 运行截图

> *(截图待补充)*

---

## 🚀 快速开始

### 前置条件

- **Chrome ≥ 120**，启用远程调试：`chrome.exe --remote-debugging-port=9222`
- **WorkBuddy** 已安装（[下载](https://www.codebuddy.cn/workbuddy)）
- **chrome-devtools MCP** 已在 WorkBuddy 中配置连接
- **抖音已在浏览器中登录**

### 安装步骤

1. 克隆本仓库（或下载 `douyin-traffic-psy/` 目录）
2. 将 `config.example.json` 复制为 `config.json`，按需填写你的话题和回复模板
3. 在 WorkBuddy 中加载该目录作为技能

```bash
git clone https://github.com/ljyoungs/AgentSkills.git
cd AgentSkills/douyin-traffic-psy
cp config.example.json config.json
# 编辑 config.json，填入你的话题配置
```

### 运行环境诊断

```
在 WorkBuddy 对话中输入：
检查 douyin-traffic-psy 环境
```

或直接运行：

```bash
python scripts/setup_wizard.py check
```

### 开始引流扫描

```
在 WorkBuddy 对话中输入：
跑一遍，主题 云南旅游攻略，不点击回复评论先
```

---

## 📁 文件结构

```
douyin-traffic-psy/
├── SKILL.md                    # WorkBuddy 技能入口（SOP + 故障排查）
├── config.example.json         # 示例配置（复制后重命名为 config.json）
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

## ⚙️ 配置说明

编辑 `config.json`（从 `config.example.json` 复制）：

```json
{
  "topics": [
    {
      "name": "我的话题",
      "search_keyword": "搜索关键词",
      "enabled": true,
      "keywords": ["求推荐", "怎么", "多少钱"],
      "reply_templates": ["你的回复模板1", "你的回复模板2"],
      "max_videos": 3,
      "max_replies_per_video": 1,
      "max_daily_replies": 15
    }
  ],
  "global_settings": {
    "reply_interval_seconds": 30,
    "max_daily_total_replies": 50,
    "captcha_detection": true,
    "comment_freshness_days": 7
  }
}
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
