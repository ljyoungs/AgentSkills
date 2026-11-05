# 通用图片生成视频 · image-to-video

让已有的人物、产品、插画或场景图片产生主体动作或场景变化，可供任何剪辑项目单独调用。

安装完整目录，上传图片后说：

```text
使用 image-to-video，让这张图片里的人物自然低头、轻轻拨动琴弦，再抬头微笑，保持完整人物和乐器。
```

也可描述产品旋转、场景变化等动作，但每种素材都需要单独验收，不把一个人物镜头的成功推广为所有素材已验证。

具体安装目录：

```text
https://github.com/ljyoungs/AgentSkills/tree/main/skills/content-creation/image-to-video
```

Codex 可用 `$skill-installer` 安装，或复制至项目 `.agents/skills/image-to-video/`；参见 [OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。其它客户端按其技能和工具接入方式处理；未做每个客户端的端到端兼容测试。

## 运行条件

Python 3.10+、FFmpeg／FFprobe、`python -m pip install -r requirements.txt`，以及可用图生视频服务。包中附公开 LTX-2.3 演示的客户端适配脚本，不含模型权重或免费 GPU 保证。可优先使用当前智能体已经接入的其它图生视频工具。

读 [SKILL.md](SKILL.md) 和 [操作方法](references/workflow.md)。本包独立于音乐，不绑定某个女孩、乐器、画幅、时长或视频模板。输出原片、默认静音成片、事件回执及抽帧检查。不能把图片缩放推拉称作人物真的活动。

## 验证范围

脚本源于实际跑通过的图片＋文字动作路线。公开包有本地模拟服务行为测试和真实 FFmpeg 解码测试，覆盖未知提交、空错误、下载恢复和声音选择；这些测试不消费远端 GPU。公共服务不保证永久可用；WorkBuddy、豆包等客户端的端到端执行未实测。运行后的技术通过不等于审美已批准。
