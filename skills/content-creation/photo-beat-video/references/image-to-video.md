# 随包的图生视频适配器

`scripts/image_to_video.py` 接收一张静态参考图和动作描述，调用 [LTX-2.3 公共演示](https://huggingface.co/spaces/linoyts/LTX-2-3-First-Last-Frame)。这是图片＋文字动作条件，没有视频动作迁移输入。

```bash
python -X utf8 scripts/image_to_video.py plan --image guitar.png --prompt-file motion.txt --duration 6
python -X utf8 scripts/image_to_video.py doctor
python -X utf8 scripts/image_to_video.py generate --image guitar.png --prompt-file motion.txt --duration 6 --out new-motion-run
python -X utf8 scripts/image_to_video.py resume --run-dir existing-motion-run
```

`plan` 离线；`doctor` 只读接口结构，不保证 GPU 配额；`generate` 上传并单次提交；`resume` 只恢复同一任务查询／下载，不重新生成。

输出保留 `source.mp4`，默认将其视频轨复制为静音 `result.mp4`，由照片卡点脚本负责固定配乐。明确需要模型音频时可以用 `--audio-mode model`，本模板仍默认关闭。

公共演示可能排队、限额、失效或更改接口。空错误只记录原因未知；没有事件编号时不能重发任务。当前默认适配短镜头，服务具体时长、尺寸约束还会再检查。生成失败不要假称还有后台任务，不自动升级或购买。
