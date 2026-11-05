# 照片一键节奏视频 · photo-beat-video

当前版本：**v1.1.0**。

上传照片，说一句话，助手按固定配乐制作视频。包含原图卡点与“原图 → 甜酷造型 → 人物动态 → 鼓点定格”两种流程。

## 怎么用

还没安装、但聊天工具能够读取 GitHub 并安装技能时，附上图片并发这一句话：

```text
请安装并使用 https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/photo-beat-video ，把这些照片做成甜酷摇滚卡点视频，使用固定配乐，交付MP4。
```

先把**完整技能目录**导入支持 Agent Skills 且可以执行脚本的工具。安装与运行依赖只需准备一次，后续只传图片：

```text
使用 photo-beat-video，把这些照片做成温柔可爱又很飒的甜酷摇滚卡点视频，使用固定配乐。
```

如果只想要原照片卡点：

```text
使用 photo-beat-video，用这些原照片做卡点视频，使用固定配乐，不生成新造型。
```

Codex 可以让 `$skill-installer` 安装这个具体目录：

```text
https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/photo-beat-video
```

也可复制到项目的 `.agents/skills/photo-beat-video/`，再用 `$photo-beat-video` 调用。安装位置和调用方式见 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。其它客户端按各自的导入方式操作。[通用提示词](references/portable-prompt.md)可以表达同样需求，但不能替代缺失的工具或安装依赖。

## 一次性运行条件

| 制作范围 | 需要的能力 |
| --- | --- |
| 原照片卡点、配乐、闪动、导出 | Python 3.10+、本目录 requirements.txt 中的库、FFmpeg／FFprobe、首次下载音乐的网络连接 |
| 甜酷造型图 | 当前聊天环境能够参考上传照片生成或编辑图片，且有可用额度 |
| 人物真正动起来 | 可用的图生视频工具，或随包的公开 LTX 演示适配器及其当时可用的免费 GPU 配额 |

```bash
python -m pip install -r requirements.txt
ffmpeg -version
ffprobe -version
```

用户无需自己写代码、准备音乐或填时码；具备终端执行能力的助手处理命令。工作环境的安装、联网和工具授权仍按客户端规则执行。

## 固定配乐怎么来

首次运行自动从[配置中的固定音源](references/template.json)下载，校验 SHA256，转 AAC 后缓存。以后直接复用缓存，无需再次上传音乐。默认缓存为用户目录 `.cache/agent-skills/photo-beat-video/`，可用 `PHOTO_BEAT_CACHE` 指定其它位置。

源站不可用、拒绝访问或文件变化时会报错；不会换成“相似歌曲”，也不承诺链接永久有效。第三方原始音乐、个人照片和家庭视频不放入仓库，具体分发边界见 [NOTICE](NOTICE.md)。

## 兼容性与费用

| 环境 | 当前范围 |
| --- | --- |
| 本地 Python＋FFmpeg | 可执行配乐缓存、照片剪辑、动态区间剪辑与定格，附离线行为测试 |
| Codex 等具备脚本和图像工具的智能体 | 可以按 SKILL 编排；出图和在线生成能力由实际账户提供 |
| WorkBuddy | 可以按其技能与工具入口接入；本公开包未完成该客户端端到端实测 |
| 豆包普通聊天 | 可参考提示词，不能仅因能够读图片就保证安装并执行此 Python 包；按实际提供的生图、生视频及剪辑功能操作 |

脚本不调用付费 API、不自动购买或充值。聊天工具、出图与图生视频的免费额度各自计算；安装本技能不等于所有生成免费或无限次。默认不公开发布任何成果。

## 多人照片与生成受阻

可将不同人物的完整造型图与合照按顺序穿插；保留各自原本外貌、年龄和持物，风格随实际人物与用户要求调整。`--styled` 支持一张或多张，推荐精选2–3张，明确需要时可增加；`--styled-seconds` 可缩短停留，`--max-opening` 可保留更多开头原图。实际时长仍须落在固定音轨内，不额外复制特写凑长度。

在线生成没有额度或用户想自行操作时，助手可运行随包的 `image_to_video.py handoff`，离线交付参考图、完整动作提示词、参数及说明。之后接收原始MP4、检查，再继续原剪辑。随包客户端使用匿名请求，网页登录不自动提供账号额度；手动包不等于视频已生成。具体判断见 [图生视频操作](references/image-to-video.md)。

## 助手执行入口

读 [SKILL.md](SKILL.md)，甜酷流程再读 [造型和动作设计](references/sweet-cool-rock.md)。单独复用图生视频可用仓库里的独立 image-to-video 包；本包已带所需适配脚本，不强制安装第二个包。

本地渲染生成 `result.mp4`、`plan.json`、`delivery.json` 和 `qa/`。原始素材与前版均保留。测试和限制见 [验证记录](references/validation.md)。
