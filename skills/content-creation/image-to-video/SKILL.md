---
name: image-to-video
description: 将已有图片中的人物、产品、插画或场景生成真正有主体动作或场景变化的视频。用于“让这张图动起来”“图片生成视频”等请求；独立于配乐、题材和剪辑项目。
---

# 通用图片生成视频

接收图片和动作意图，交付可播放动态素材及真实制作记录。用户只需描述想看见的动作，助手负责解析附件、看图、执行与检查。

1. 查看图片，确认要保留的主体、年龄、比例、持物、产品结构、文字与环境。用少量可见动作设计一个短镜头；按图片选择画幅，不固定儿童、吉他、竖版或配乐。
2. 优先使用当前环境真实可用且符合要求的图生视频工具。需要复用公开 LTX 路线时读 [操作方法](references/workflow.md)。公开演示曾成功，不保证服务永久在线、免费额度或所有素材质量。
3. 单次提交，保存图片哈希、提示词、参数、服务、事件编号、原片和状态。上传、提交、生成完成、下载、技术检查和审美通过分别记录。未知提交结果先恢复查询，不重复提交。
4. 完整解码并查看首中末与关键动作帧，检查脸、手、道具、边缘、纹理漂移和场景稳定。自动帧差只能说明像素变化，不能证明人物自然运动。必要时选取合格区间。
5. 交付 MP4，说明方法、时长、声音和明显局限。保留原片；用户指定配乐由调用方处理。未经请求不发布、不购买或充值。

多人画面先明确每个人的位置、外貌和持物，再安排简单的相互回应；用户认可的参考图优先，不因“更帅／更美”自行换脸或重做已否定的造型。人物自然动作仍需逐次验收，多人同台效果未因单人成功而获得验证。

依赖 Python 3.10+、requests、Pillow、FFmpeg 和 FFprobe。脚本相对本技能目录，实际执行时解析绝对路径：

```bash
python -X utf8 scripts/image_to_video.py plan --image input.png --prompt-file motion.txt --duration 6
python -X utf8 scripts/image_to_video.py doctor
python -X utf8 scripts/image_to_video.py generate --image input.png --prompt-file motion.txt --duration 6 --out new-run
python -X utf8 scripts/image_to_video.py resume --run-dir existing-run
python -X utf8 scripts/image_to_video.py handoff --image input.png --prompt-file motion.txt --duration 5 --out new-handoff
python -X utf8 scripts/image_to_video.py check --video existing.mp4 --out new-check
```

`plan` 离线；`doctor` 只读检查接口；`generate` 单次提交；`resume` 只查询／下载同一任务；`status` 是保存状态，不是后台实时状态。每约60秒报告最后确认的阶段；空错误不猜原因，提交结果未知不自动重发。

当前随包客户端是匿名请求，不读取浏览器登录状态、Cookie 或令牌。`doctor` 接口可达不代表账号有额度；浏览器登录也不会让此脚本自动获得账号额度。额度耗尽时保留回执及提供方倒计时，不轮换账号绕过限额；已确认失败的任务不会因 `resume` 变成新生成。

用户要求自行生成，或自动操作受阻需要交接时，用 `handoff` 离线准备参考图、完整提示词、参数与说明；交付实际文件，不只报一个模型名。说明尚未上传、尚未生成。用户返回 MP4 后用 `check` 验证，再交回剪辑项目。登录、额度、浏览器限制及判断表见 [操作方法](references/workflow.md)。

默认生成静音 `result.mp4` 并保留 `source.mp4`。用户确实需要模型声音时传 `--audio-mode model`。默认输出当前工作目录 `outputs/image-to-video/` 的新子目录；当前用户指定的磁盘和目录优先。

普通照片推拉、仅写提示词、已有视频的人物替换，不自动进入本流程。此适配器只提交图片＋文字动作，没有驱动视频输入，不能声称完成视频动作迁移。

安装与边界见 [README](README.md)，来源见 [NOTICE](NOTICE.md)。
