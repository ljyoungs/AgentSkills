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
```

默认按图片比例选择长边约1280、边长32倍数的尺寸；可显式传 `--width` 和 `--height`，必须成对给出。默认6秒，适配器处理1–10秒短镜头，服务当时的其它约束仍适用。

`doctor` 能访问参数结构不代表免费 GPU 有余额。首次任务单次提交后保存事件；等待或下载失败，用 `resume` 恢复同一事件。提交超时且没有事件编号时，状态是未知，不得重新提交。服务返回空错误时原因未知，不能直接解释为额度耗尽。

运行会保留 source.mp4，默认 result.mp4 删除生成音轨；加 `--audio-mode model` 才保留模型声音。两个文件均不自动叠加配乐。

## 检查

脚本完整解码并抽7帧，检查时长、分辨率、音轨和帧差。助手还需看真实画面：脸、手、产品结构、持物、纹理与画面边缘是否稳定，动作是否真实发生。帧差大也可能只是镜头移动或背景变化。

交付区分技术检查、模型看帧和用户审美批准；不要把离线测试写成远端生成成功。免费额度不足则保留成果并说明，未经授权不购买或充值。
