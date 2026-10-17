# 老高叙事方法 Skill

**社区非官方版 · v1.0.0 · MIT · 中文优先 · 无必需外部服务**

输入选题和资料，得到有观看动机、有逻辑、可审核的原创故事方案。适合科普、知识解说和案例视频，提供选题、结构、完整口播／分镜以及内容与发布包装审核四个入口。

“AI蒸馏”在这里指将有限公开样本中可观察的讲述方法，以及实际改稿反馈整理成可复用指令。它不是模型权重训练、真人替身或官方出品，不包含真人声音。

## 开始使用

将**本目录整体**导入支持Agent Skills的工具，保留`references/`、`examples/`等相对目录。无需API密钥、浏览器或付费配音服务即可使用文字策划能力；实际事实检索能力取决于所用客户端。

给支持读取GitHub目录的工具这个地址，并要求读取`SKILL.md`及当前任务需要的参考文件：

```text
https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/laogao-story-advisor
```

Codex可使用：

```text
$skill-installer 安装 https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/laogao-story-advisor
```

也可将本目录复制到项目的`.agents/skills/laogao-story-advisor/`，然后请求：

```text
$laogao-story-advisor
选题：没有大脑的大肠杆菌，怎么找到食物？
受众：普通中文观众。
资料：我提供的两份来源摘录。
先给结构：用“找吃的”贯穿；不要在开头把全部机制揭晓。
```

Codex的目录发现与调用方式参见[OpenAI官方说明](https://learn.chatgpt.com/docs/build-skills)。其它客户端按其技能导入方式操作；不宣称本包已在所有平台完成实测。只粘贴`SKILL.md`会缺少参考材料，应同时提供相关文件。

## 可以怎么用

| 入口 | 示例要求 | 结果 |
| --- | --- | --- |
| 选题 | 根据资料找一个最值得追问的问题 | 题眼、观众收益、线索与缺口 |
| 结构 | 先给一条完整故事线 | 每段观众猜想、线索、理解变化与下一问 |
| 完整稿 | 把已确认结构写成自然口播和分镜 | 原创逐字稿、可见动作、来源身份与素材状态 |
| 审稿 | 检查我的稿、封面、标题和正文是否抓人 | 具体问题、返工内容和有范围的复核结论 |

输出范围由请求决定。用户只讨论题眼时不生成整套剧本；本包不自动生成配音、渲染视频、上传或公开发布。

## 看实际示例

- [大肠杆菌：输入与科学资料边界](examples/ecoli/input.md)
- [大肠杆菌：分享版故事结构与原创开头](examples/ecoli/structure.md)
- [AI工具：仅依赖给定虚构情境的完整短稿](examples/agent-demo.md)
- [审稿：发现问题、改写与复核](examples/review-demo.md)

大肠杆菌来自真实创作经历，但这里的结构是重新整理的文字示范，不冒充已重新拍成的视频。AI工具案例为明确标注的虚构示意，没有运行任何真实服务。

## 能证明什么

本版完成技能格式、相对引用、独立文件包及案例检查；具体方法与限制见[方法证据](references/evidence.md)。内容与封面审核是编辑判断，不保证传播结果；实际成片的声音和动态节奏需以真实视听检查为准。

本目录可独立使用；[MIT许可证](LICENSE)随包提供，[NOTICE](NOTICE.md)说明第三方参考的分发边界。
