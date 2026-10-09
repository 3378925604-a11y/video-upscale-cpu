---
name: video-upscale-cpu
description: '视频补分辨率/升 2K/去色带/画面发糊发虚——任意视频通用（动效信息图、2D/3D 动画、实拍、录屏、电影剧集片段均可）的纯 CPU ffmpeg 修复链：deband 去色带 → hqdn3d 去压缩噪 → lanczos 放大 → CAS 锐化。零显存、零下载、免 AI、免注册。当用户发来视频说"补分辨率""升到 2K""画面糊/有色带""帮我放大""画质修复"时触发。对实拍素材同样有效；若追求实拍纹理的极致重建，可在本链基础上再叠加 AI 超分作为可选进阶。'
---

# video-upscale-cpu — 视频补分辨率（纯 CPU 通用链）

一条实测验证的 ffmpeg 修复链：**deband 去色带 → hqdn3d 去压缩噪 → lanczos 放大到 2560×1440 → CAS 0.6 锐化**，x264 crf15，音轨原样 copy。纯 CPU，零显存，速度约 RTF 1~3（161 秒素材几分钟跑完）。**任意视频通用**——动效图、动画、实拍、录屏、电影片段都能吃。

## 修复的三类典型病灶

1. **黑底/渐变色带（banding）**——deband 主治，动画和暗场实拍都常见
2. **压缩糊掉的小字与边缘**——lanczos+CAS 主治，信息图、录屏、字幕全受益
3. **压缩噪点与 General 糊感**——hqdn3d 主治

## 一键脚本（封装了全部坑）

```bash
python scripts/upscale2k.py <源视频> [输出路径]
```

依赖：`ffmpeg/ffprobe` 在 PATH（[下载](https://ffmpeg.org/download.html) 或 `winget install Gyan.FFmpeg`）；`Pillow + numpy` 可选（只影响自动验收对比图）。

脚本自动做：ffprobe 探源 → 目标尺寸计算（源高 ≥1440 则只修复不放大）→ 跑链 → 完整性校验（moov 可读 / 时长对齐 / 音轨起点=0）→ 输出同帧 1:1 对比图（旧版 nearest 对齐到同尺寸 vs 新版）+ 边缘能量比报告。

## 手动命令（等价）

```bash
ffmpeg -y -i <源> -vf "deband,hqdn3d=1.5:1.5:6:6,scale=2560:1440:flags=lanczos,cas=0.6"   -c:v libx264 -crf 15 -preset medium -c:a copy <输出>
```

## 按内容类型微调（可选，不调也能跑）

| 内容 | 建议微调 |
|---|---|
| 动效图/信息图（黑底小字） | 默认即可；小字过锐把 `cas=0.6` 降到 0.4 |
| 2D 动画 | 默认即可；色带重可再叠一次 deband |
| 实拍真人 | `hqdn3d` 前两位降到 1（保留胶片颗粒）；追求毛孔级纹理重建可再叠加 AI 超分作为进阶 |
| 录屏/教程 | 默认；文字发虚重点看 CAS |

## 🔴 三条硬坑（每条都实撞过）

1. **`lanczos` 不是独立滤镜**——必须写 `scale=2560:1440:flags=lanczos`，写 `lanczos=2560:1440` 直接 Invalid argument。
2. **mp4 的 moov 索引转码结束才写入**——跑一半打开输出必报 "Invalid data / 无法打开"，这不是坏了，等跑完。
3. **二手转码版不可作源**——QQ/微信等 IM 转码会抽帧（实测 4842→4830 帧）+时间戳损伤，用它的视频轨配原版音轨 = 音画错位（前几秒没声）。错位排查：`ffprobe -select_streams a:0 -show_entries stream=start_time` + `silencedetect` 查音轨起点。

## 验收口径

- 同帧 1:1 像素对比：旧版用 `flags=neighbor` 放大到同尺寸，边缘能量比（新/旧）在 **1.05~1.15** 为正常增益；明显低于 1.0 = 链子起反作用，查参数。
- 小字边缘、黑底色带两个观察点**打开对比图亲眼确认**，量化指标只是旁证。
- 音轨：输出 `start_time=0` + 开头 3 秒 volumedetect 有响度。
