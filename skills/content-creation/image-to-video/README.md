# 通用图片生成视频 · image-to-video

当前版本：**v1.1.0**。

让已有的人物、产品、插画或场景图片产生主体动作或场景变化，可供任何剪辑项目单独调用。

安装完整目录，上传图片后说：

```text
使用 image-to-video，让这张照片里的人物轻轻转头、自然微笑，保持原人物、衣服和完整构图。
```

也可描述产品旋转、场景变化等动作，但每种素材都需要单独验收，不把一个人物镜头的成功推广为所有素材已验证。

第一次使用、且智能体能读取 GitHub 与安装技能时，也可直接发：

```text
请安装并使用 https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/image-to-video ，让这张图按我的描述自然动起来，保留人物与完整道具，交付MP4。
```

具体安装目录：

```text
https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/image-to-video
```

Codex 可用 `$skill-installer` 安装，或复制至项目 `.agents/skills/image-to-video/`；参见 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。其它客户端按其技能和工具接入方式处理；未做每个客户端的端到端兼容测试。

## 运行条件

Python 3.10+、FFmpeg／FFprobe、`python -m pip install -r requirements.txt`，以及可用图生视频服务。包中附公开 LTX-2.3 演示的客户端适配脚本，不含模型权重或免费 GPU 保证。可优先使用当前智能体已经接入的其它图生视频工具。

读 [SKILL.md](SKILL.md) 和 [操作方法](references/workflow.md)。本包独立于音乐，不绑定某个女孩、乐器、画幅、时长或视频模板。输出原片、默认静音成片、事件回执及抽帧检查。不能把图片缩放推拉称作人物真的活动。

## 额度与手动接续

随包 Python 客户端使用**匿名请求**，没有浏览器登录或令牌接入功能。在网页登录账号不会改变脚本的请求身份。`doctor` 只检查接口结构，不检查账号余额。免费 GPU 耗尽后按页面倒计时等待；免费范围以 [Hugging Face 当前说明](https://huggingface.co/docs/hub/spaces-zerogpu#usage-tiers)及实际服务为准。

需要自己在网页生成时，让助手运行：

```bash
python -X utf8 scripts/image_to_video.py handoff --image reference.png --prompt-file motion.txt --duration 5 --out new-handoff
```

这会离线打包 `reference.png`、`prompt.txt`、`handoff.json` 和 `使用说明.txt`，不登录、不上传、不消耗 GPU。参数是建议值，仍需按当前页面支持范围设置。仅凭这个包不能宣称视频已生成。生成后把原始 MP4 交回助手执行 `check`、看帧并用于原剪辑。

## 验证范围

脚本源于实际跑通过的图片＋文字动作路线。公开包有本地模拟服务行为测试和真实 FFmpeg 解码测试，覆盖未知提交、空错误、下载恢复和声音选择；这些测试不消费远端 GPU。公共服务不保证永久可用；WorkBuddy、豆包等客户端的端到端执行未实测。运行后的技术通过不等于审美已批准。

v1.1.0新增额度错误分类、倒计时保留、离线手动交接、中文路径CLI与独立安装包一致性检查；2026-11-05整仓29项测试通过。测试未上传私人图片、未提交新的远端生成，多人互动生成仍未验证成功。
