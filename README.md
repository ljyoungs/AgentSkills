# AgentSkills

按用途组织的智能体技能库。每个技能都有自己的用途说明、依赖和一句话安装指令。

## 分类与技能目录

| 分类 | 技能 | 适用场景 | 运行条件 |
| --- | --- | --- | --- |
| 内容创作 | [老高叙事方法](skills/content-creation/laogao-story-advisor/) | 从资料整理选题、故事结构、口播和分镜 | 文字策划可离线使用 |
| 内容创作 | [照片一键节奏视频](skills/content-creation/photo-beat-video/) | 用照片和固定配乐制作节奏视频 | Python、FFmpeg；生成造型和人物动态还需要相应工具及额度 |
| 社媒运营 | [抖音智能引流助手](skills/social-media/douyin-traffic-psy/) | 评论筛选、关键词匹配和半自动回复 | WorkBuddy、Chrome、Chrome DevTools MCP；详见技能页 |
| 求职工具 | [BOSS 直聘简历同步](skills/job-search/boss-resume-sync/) | 对照定稿、增量更新在线简历、回读核验 | 在线操作需要已登录的 BOSS 页面和浏览器控制能力 |

机器可读索引见 [catalog.json](catalog.json)。

## 一句话安装

点开上表中的技能，把「一句话安装」里的整句发给 **Codex、WorkBuddy 或其他支持安装技能的智能体**。智能体按链接获取完整技能包，安装到当前客户端并确认能否调用。安装后，在对话里用技能名说明任务即可。

安装需要客户端能访问 GitHub 并安装技能。浏览器、脚本和模型额度等运行条件见各技能页。客户端兼容性以实际安装及调用结果为准。

## 仓库目录说明

| 路径 | 内容 |
| --- | --- |
| [`skills/`](skills/) | 正式技能包。分为内容创作 `content-creation/`、社媒运营 `social-media/`、求职工具 `job-search/`。包内 `README.md` 面向使用者，`SKILL.md` 定义智能体工作流。 |
| [`evaluations/`](evaluations/) | 技能试用记录和复核报告。 |
| [`scripts/`](scripts/) | 仓库目录与链接的校验脚本。 |
| [`tests/`](tests/) | 仓库校验和技能组件的回归测试。 |
| [`AgentSkills/`](AgentSkills/douyin-traffic-psy/README.md) | 旧抖音技能链接的迁移说明，指向上表的正式技能包。 |

## 维护与许可

新增技能放在 `skills/<分类>/<技能名>/`，同步更新首页技能表和 `catalog.json`。各技能页使用统一的一句话安装入口。校验方式与维护约定见 [AGENTS.md](AGENTS.md)。

仓库原创内容采用 [MIT](LICENSE) 许可。第三方材料的来源和分发说明见各技能包的许可文件。
