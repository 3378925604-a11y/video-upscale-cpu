---
name: video-upscale-cpu
description: 'Video resolution boost / upscale to 2K / remove banding / fix soft blurry footage — for motion-graphics, infographic, 2D-animation and flat-design videos. Pure CPU ffmpeg chain (deband → denoise → lanczos upscale → CAS sharpen), zero VRAM, zero downloads, no AI needed. Trigger when the user sends a video asking to "upscale", "fix resolution", "it looks soft/blurry", "there is banding" and the content is graphics/text/animation. Real-life camera footage is a suboptimal case for this chain (use AI super-resolution for texture reconstruction instead) — the script detects and warns.'
---

# video-upscale-cpu — 动效图视频补分辨率（纯 CPU 链）

一条实测验证的 ffmpeg 修复链：**deband 去色带 → hqdn3d 去压缩噪 → lanczos 放大到 2560×1440 → CAS 0.6 锐化**，x264 crf15，音轨原样 copy。纯 CPU，零显存，速度约 RTF 1~3（161 秒素材几分钟跑完）。

## 适用判据（动手前必须先做）

1. **ffprobe 探源**：分辨率、时长、音视频流。
2. **抽帧看内容**：黑底扁平图形/文字/图表/2D 动画 → 本链对口（效果见 `docs/` 前后对比图）；**实拍真人 → 本链是次优解**（实拍的增益在重建皮肤毛发纹理，应走 AI 超分），如实告知并停。
3. **源文件必须是原始版**：二手转码版（QQ/微信等 IM 压过的）已被抽帧+时间戳损伤，做出来音画错位——实测踩过的坑。

## 一键脚本（封装了全部坑）

```bash
python scripts/upscale2k.py <源视频> [输出路径]
```

依赖：`ffmpeg/ffprobe` 在 PATH；`Pillow + numpy`（仅验收对比图用，缺了不影响成片）。

脚本自动做：ffprobe 探源 → 目标尺寸计算（源高 ≥1440 则只修复不放大）→ 跑链 → 完整性校验（moov 可读 / 时长对齐 / 音轨起点 =0）→ 输出同帧 1:1 对比图（旧版 nearest 对齐到同尺寸 vs 新版）+ 边缘能量比报告。

## 手动命令（等价）

```bash
ffmpeg -y -i <源> -vf "deband,hqdn3d=1.5:1.5:6:6,scale=2560:1440:flags=lanczos,cas=0.6" \
  -c:v libx264 -crf 15 -preset medium -c:a copy <输出>
```

参数微调：小字过锐 → `cas=0.6` 降到 0.4；色带残留 → 保留 deband 在链首或再叠加一次；压缩噪重 → hqdn3d 前两个值升到 2。

## 🔴 三条硬坑（每条都实撞过）

1. **`lanczos` 不是独立滤镜**——必须写 `scale=2560:1440:flags=lanczos`，写 `lanczos=2560:1440` 直接 Invalid argument。
2. **mp4 的 moov 索引转码结束才写入**——跑一半打开输出必报 "Invalid data / 无法打开"，这不是坏了，等跑完。
3. **二手转码版不可作源**——IM 转码会抽帧（实测 4842→4830 帧）+时间戳损伤，用它的视频轨配原版音轨 = 音画错位（前几秒没声）。音画错位排查：`ffprobe -select_streams a:0 -show_entries stream=start_time` + `silencedetect` 查音轨起点。

## 验收口径

- 同帧 1:1 像素对比：旧版用 `flags=neighbor` 放大到同尺寸，边缘能量比（新/旧）在 **1.05~1.15** 为正常增益；明显低于 1.0 = 链子起反作用，查参数。
- 小字边缘、黑底色带两个观察点**必须打开对比图亲眼确认**，量化指标只是旁证。
- 音轨：输出 `start_time=0` + 开头 3 秒 volumedetect 有响度。
