# AgentSkills

个人维护的 **Agent Skill 总仓库**。按用途分类，每个技能有独立入口、依赖说明和使用示例，可单独下载或导入；新增技能继续放在本仓库。

## 分类与技能目录

| 分类 | 技能 | 用途 | 版本／依赖 |
| --- | --- | --- | --- |
| **内容创作** `content-creation` | [老高叙事方法 · laogao-story-advisor](skills/content-creation/laogao-story-advisor/) | 选题、递进故事结构、完整口播／分镜、内容与发布包装审核 | v1.0.0；文字策划无必需外部服务 |
| **社媒运营** `social-media` | [抖音智能引流 · douyin-traffic-psy](skills/social-media/douyin-traffic-psy/) | 评论扫描、关键词匹配和半自动回复 | 原有V3系列；需要其README所列Chrome、WorkBuddy与MCP环境 |

机器可读目录：[catalog.json](catalog.json)。类别按实际技能扩展，不预建空类别。

## 推荐先试

```text
使用 laogao-story-advisor。
选题：没有大脑的大肠杆菌，怎么找到食物？
根据我提供的资料先给故事结构，再检查是否提前泄底、逻辑跳跃和结尾无回报。
```

查看[输入材料](skills/content-creation/laogao-story-advisor/examples/ecoli/input.md)、[结构示范](skills/content-creation/laogao-story-advisor/examples/ecoli/structure.md)和[审稿示范](skills/content-creation/laogao-story-advisor/examples/review-demo.md)。内容来自方法整理与实际创作反馈，非老高本人或官方作品，不含真人声音。

## 安装与使用

先选一个技能，**复制完整技能目录**，不要把整个分类目录当成一个技能。

```bash
git clone https://github.com/ljyoungs/AgentSkills.git
```

例如，老高叙事Skill位于：

```text
AgentSkills/skills/content-creation/laogao-story-advisor/
```

Codex用户可把该目录复制到项目的`.agents/skills/laogao-story-advisor/`，或让`$skill-installer`安装下面这个**具体技能目录**：

```text
https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/laogao-story-advisor
```

然后用`$laogao-story-advisor`调用。[Codex技能目录与调用方式](https://learn.chatgpt.com/docs/build-skills)以官方说明为准。其它支持Agent Skills的工具按其导入方式加载，或者要求工具读取`SKILL.md`及相关参考文件；只读一个文件可能缺少模板。不同技能的运行依赖不同，不把“格式可读取”写成“所有平台都已测试”。

## 目录规范

```text
skills/
  content-creation/
    laogao-story-advisor/
      SKILL.md
      README.md
      LICENSE
      NOTICE.md
      agents/openai.yaml
      references/
      examples/
  social-media/
    douyin-traffic-psy/
catalog.json
scripts/validate_catalog.py
```

新增技能使用`skills/<category>/<skill-name>/`，更新`catalog.json`及上方表格。每个技能的`SKILL.md`须说明适用任务与交付范围；项目路径、凭据、私有声音／媒体和运行数据不随包分享。可执行脚本和自动化依赖在对应README中说明。

本地检查：

```bash
python scripts/validate_catalog.py
python -m unittest discover -s tests -v
```

这检查目录、链接与可分发边界，不会执行社媒回复、浏览器登录或付费生成，也不证明语义效果或实际平台兼容性。

## 原目录迁移

2026-10-17将原`AgentSkills/douyin-traffic-psy/`整理到`skills/social-media/douyin-traffic-psy/`。旧目录保留[迁移说明](AgentSkills/douyin-traffic-psy/README.md)。抖音技能的执行指令、配置与脚本保持原内容，本次只移动目录并修正README安装路径。旧安装用户若要获取后续更新，请采用新地址。

## 许可

本仓库自行编写内容按[MIT](LICENSE)分享；技能包随附的许可与第三方声明需一并保留。老高Skill的[NOTICE](skills/content-creation/laogao-story-advisor/NOTICE.md)解释研究参考与分发范围，链接指向的第三方内容仍适用各自许可。
