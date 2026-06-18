# AgentSkills

> 可跨平台加载的智能体技能包 — 支持 WorkBuddy · Kimi · OpenClaw 及任意兼容智能体平台

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-WorkBuddy%20%7C%20Kimi%20%7C%20OpenClaw-blue)

---

## 技能列表

| 技能 | 说明 | 版本 |
|------|------|------|
| [douyin-traffic-psy](./douyin-traffic-psy/) | 抖音智能引流助手 — 评论扫描 + 关键词匹配 + 半自动回复 | V3.0 |

---

## 使用方式

### 方式一：让智能体自动安装（最简单）

直接把技能目录的 GitHub 链接发给你用的智能体，让它自动读取安装：

```
https://github.com/ljyoungs/AgentSkills/tree/main/douyin-traffic-psy
```

示例指令：
> 「帮我安装这个技能：https://github.com/ljyoungs/AgentSkills/tree/main/douyin-traffic-psy」

支持该方式的平台：WorkBuddy、OpenClaw、以及任何能读取 GitHub 链接的智能体。

---

### 方式二：本地克隆后导入

```bash
git clone https://github.com/ljyoungs/AgentSkills.git
```

克隆后，在各平台按以下方式加载：

| 平台 | 加载方式 |
|------|---------|
| **WorkBuddy** | 设置 → 技能 → 导入本地目录，选择技能文件夹 |
| **Kimi** | 发送技能目录 GitHub 链接，告诉 Kimi 读取 `SKILL.md` 并按说明执行 |
| **OpenClaw** | 导入技能文件夹，或直接粘贴 GitHub 链接让其自动拉取 |
| **其他平台** | 将 `SKILL.md` 的内容粘贴到系统提示词或技能配置区域 |

---

### 方式三：直接复制 SKILL.md 内容

每个技能目录下都有 `SKILL.md`，内容即技能的完整指令。  
将其粘贴到任意支持自定义系统提示的智能体即可使用，无需安装。

---

## 技能结构说明

每个技能目录包含：

```
douyin-traffic-psy/
├── SKILL.md        # 技能核心指令（平台无关）
├── README.md       # 技能详细说明与配置
└── ...             # 其他辅助文件
```

---

## License

MIT © [ljyoungs](https://github.com/ljyoungs)
