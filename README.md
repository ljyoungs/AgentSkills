# AgentSkills

个人维护的 **Agent Skill 总仓库**。按用途分类，每个技能有独立入口、依赖说明和使用示例，可单独下载或导入；新增技能继续放在本仓库。

## 分类与技能目录

| 分类 | 技能 | 用途 | 版本／依赖 |
| --- | --- | --- | --- |
| **内容创作** `content-creation` | [老高叙事方法 · laogao-story-advisor](skills/content-creation/laogao-story-advisor/) | 选题、递进故事结构、完整口播／分镜、内容与发布包装审核 | v1.1.0；文字策划无必需外部服务 |
| **内容创作** `content-creation` | [照片一键节奏视频 · photo-beat-video](skills/content-creation/photo-beat-video/) | 上传图片，固定配乐，多人造型穿插／人物动态／鼓点定格 | v1.1.0；Python、FFmpeg，完整同款另需生图和图生视频额度 |
| **内容创作** `content-creation` | [通用图片生成视频 · image-to-video](skills/content-creation/image-to-video/) | 图片生成动态素材，支持失败恢复与离线手动交接，独立于配乐与剪辑 | v1.1.0；Python、FFmpeg、可用图生视频服务 |
| **社媒运营** `social-media` | [抖音智能引流 · douyin-traffic-psy](skills/social-media/douyin-traffic-psy/) | 评论扫描、关键词匹配和半自动回复 | 原有V3系列；需要其README所列Chrome、WorkBuddy与MCP环境 |

机器可读目录：[catalog.json](catalog.json)。类别按实际技能扩展，不预建空类别。

## 推荐先试

```text
使用 laogao-story-advisor。
选题：没有大脑的大肠杆菌，怎么找到食物？
根据我提供的资料先给故事结构，再检查是否提前泄底、逻辑跳跃和结尾无回报。
```

查看[输入材料](skills/content-creation/laogao-story-advisor/examples/ecoli/input.md)、[结构示范](skills/content-creation/laogao-story-advisor/examples/ecoli/structure.md)和[审稿示范](skills/content-creation/laogao-story-advisor/examples/review-demo.md)。内容来自方法整理与实际创作反馈，非老高本人或官方作品，不含真人声音。

v1.1增加[两期原片的参照与规则映射](skills/content-creation/laogao-story-advisor/references/episode-mapping.md)、[具体叙事改写手册](skills/content-creation/laogao-story-advisor/references/narrative-mechanics.md)、[大肠杆菌完整口播](skills/content-creation/laogao-story-advisor/examples/ecoli/full-script.md)与[全稿分镜](skills/content-creation/laogao-story-advisor/examples/ecoli/storyboard.md)，以及[事实正确但平淡的审稿例子](skills/content-creation/laogao-story-advisor/examples/borderline-review.md)。

[新输入文字试用记录](evaluations/laogao-story-advisor/v1.1.0/report.md)包含给定材料、两组首次答案和匿名复核。结果支持本轮交付可用，不证明稳定优于未加载Skill或已验证爆款效果。

## 上传图片做同款

安装[照片一键节奏视频](skills/content-creation/photo-beat-video/)后，附上图片并说：

```text
使用 photo-beat-video，把这些照片做成温柔可爱又很飒的甜酷摇滚卡点视频，使用固定配乐。
```

支持读取仓库和安装技能的智能体，首次也可直接发送：

```text
请安装并使用 https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/photo-beat-video ，把这些照片做成甜酷摇滚卡点视频，使用固定配乐，交付MP4。
```

用户无需上传音乐，首次自动获取并校验固定来源，以后使用本地缓存。原照片剪辑可本地执行；完整同款需要当前智能体具备参考图生图、图生视频和脚本导出能力。仅能聊天或读图的界面不保证一键成片；在线额度与免费范围由服务决定。

单独让一张图动起来，使用[通用图片生成视频](skills/content-creation/image-to-video/)。两个目录均可独立安装，不包含个人照片、家庭成片、第三方原始音轨或账号凭据。

v1.1补齐多人造型图按序穿插、每张停留时长，以及在线生成受阻后的离线交接包。额度不足、空错误、未知提交和浏览器连接失败分开处理。随包图生视频脚本使用匿名请求，网页登录不会自动给它账号额度；安装技能也不会增加模型或免费GPU。

只让图片动起来、无需这个固定配乐模板时，附图并发送：

```text
请安装并使用 https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/image-to-video ，让这张图片按我的描述自然动起来，保持主体和完整道具，交付MP4。
```

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
