# 图生视频执行方法

先查看参考图，再写动作；对于人物保留外貌、年龄和比例，对于产品保留外形、材质和可读标志，场景与插画按原画风运动。透明图先选择背景，动态图先明确所用参考帧，不能静默抛弃透明区域或动画帧。

## 公开演示适配器

服务：[LTX-2.3 First/Last Frame](https://huggingface.co/spaces/linoyts/LTX-2-3-First-Last-Frame)，客户端只提供第一张图片与文字，不上传驱动视频。公开接口的参数顺序会在上传前检查，变化时停止。

```bash
python -X utf8 scripts/image_to_video.py plan --image reference.png --prompt-file motion.txt --duration 6
python -X utf8 scripts/image_to_video.py doctor
python -X utf8 scripts/image_to_video.py generate --image reference.png --prompt-file motion.txt --duration 6 --out new-run
python -X utf8 scripts/image_to_video.py status --run-dir new-run
python -X utf8 scripts/image_to_video.py resume --run-dir new-run
python -X utf8 scripts/image_to_video.py handoff --image reference.png --prompt-file motion.txt --duration 5 --out new-handoff
python -X utf8 scripts/image_to_video.py check --video returned.mp4 --out new-check
```

默认按图片比例选择长边约1280、边长32倍数的尺寸；可显式传 `--width` 和 `--height`，必须成对给出。默认6秒，适配器处理1–10秒短镜头，服务当时的其它约束仍适用。

`doctor` 能访问参数结构不代表免费 GPU 有余额。首次任务单次提交后保存事件；等待或下载失败，用 `resume` 恢复同一事件。提交超时且没有事件编号时，状态是未知，不得重新提交。服务返回空错误时原因未知，不能直接解释为额度耗尽。

运行会保留 source.mp4，默认 result.mp4 删除生成音轨；加 `--audio-mode model` 才保留模型声音。两个文件均不自动叠加配乐。

## 登录与免费 GPU

随包客户端的请求身份是匿名：不读取浏览器会话，不读取 `HF_TOKEN`，没有已实现的令牌参数。用户网页已登录，不能据此称脚本已在使用该账号额度。需要已登录网页的生成能力时，使用当前环境可用且获准的浏览器工具或交给用户操作；不要为“接通额度”提取 Cookie 或要求把令牌贴到聊天。

[ZeroGPU 官方额度说明](https://huggingface.co/docs/hub/spaces-zerogpu#usage-tiers)在2026-11-05区分匿名、免费登录及付费档位，按首次 GPU 使用后的24小时重置；具体额度和可用模型会变化，不能硬编码成永久承诺。GPU计算时间不是视频时长。更短视频或更低分辨率不保证低于服务的最小 GPU 预约时间。

首次正常登录和已耗尽额度后的多账号轮换要区分；不建议注册／切换账号、代理或 IP 来绕过限额。不自动订阅、充值或购买。额度恢复不等于已确认失败的任务会自动继续，重新生成前应核对当前状态与用户任务是否仍有效。

## 遇到问题如何接续

| 已确认的证据 | 处理 |
| --- | --- |
| `doctor` 返回参数一致 | 只证明接口可达；账号、额度、GPU启动均未确认 |
| 有事件编号，等待／下载中断 | `resume --run-dir ...`，查询同一事件，不新提交 |
| 提交超时，无事件编号 | 保留 `submission_unknown`，查看原任务；不重复点生成 |
| 明确返回 ZeroGPU quota exceeded | 回执标为 `quota_exhausted`，保留原错误与提供方倒计时；不安排自动重试 |
| `event: error` 的内容是 `null` | 原因未知，不能归因于额度、参考图或审核 |
| 浏览器连接超时 | 如实记录连接未成功，不猜账号无额度；用户指定CDP时检查实际已有连接，不能用空白测试浏览器冒充登录会话 |
| 浏览器工具明确因网址／访问安全校验而停止 | 停止该路径，不换通道绕过限制；报告尚未上传／提交的实际状态 |
| 用户要自己操作或需要手动交接 | `handoff` 生成实际本地文件，不称为已生成视频 |

`handoff` 输出经过方向校正的完整 `reference.png`、动作 `prompt.txt`、相对文件名的 `handoff.json` 和使用说明，不裁图、不改人物，也不提交远端任务。选择当前有额度、支持首帧图生视频的模型；页面参数以当时实际控件为准。交付图片和提示词的可打开链接，不要求用户从长聊天里自行找图。

下载原始 MP4 后执行 `check`。该命令只检查，不静音或改写用户返回的文件；若剪辑项目要求原背景音乐，剪辑阶段关闭生成音轨，不能更换原配乐。

## 已验证与未验证

2026-11-05历史制作跑通过此LTX-2.3匿名路线：单人持乐器参考图＋动作文字，6秒请求、1088×1920、seed17、关闭提示词增强，实际输出约6.04秒、24fps。片段中有拨弦、摇肩与抬头动作，也存在手部／琴颈细节漂移和部分边缘问题，后续仅选用合格区间。没有提供驱动视频，不能称为演唱会动作替换。

另一次多人同台提交返回空错误；另一服务明确报过GPU额度耗尽。两者原因不能合并。本包不包含私人参考图或成片；多人联动尚未取得可交付视频，登录浏览器生成通道未完成端到端验证。当前包的模拟服务测试与历史真实生成分开记录。

## 检查

脚本完整解码并抽7帧，检查时长、分辨率、音轨和帧差。助手还需看真实画面：脸、手、产品结构、持物、纹理与画面边缘是否稳定，动作是否真实发生。帧差大也可能只是镜头移动或背景变化。

交付区分技术检查、模型看帧和用户审美批准；不要把离线测试写成远端生成成功。免费额度不足则保留成果并说明，未经授权不购买或充值。
