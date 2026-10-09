# video-upscale-cpu 🎞️

**任意视频通用补分辨率——纯 CPU ffmpeg 修复链，零显存、零下载、免 AI。**动效图、2D/3D 动画、实拍、录屏、电影剧集片段都能吃。

一条实测验证的链：`deband`（去黑底色带）→ `hqdn3d`（去压缩噪）→ `lanczos` 放大到 2560×1440 → `CAS 0.6`（锐化文字与图形边缘）。161 秒 1080p 素材几分钟跑完，输出 2K crf15，音轨原样不动。

![demo](docs/demo.gif)

*左：1080p 直接放大 · 右：本链（黑底色带与噪点差异最明显）*

## 前后对比（1:1 像素，同源画面）

| Before（1080p 直接放大） | After（本链） |
|---|---|
| ![before](docs/before_1080p_nearest.jpg) | ![after](docs/after_2k_chain.jpg) |

小字笔画、图形边缘、暗部色带三处都有可见净增益；量化口径见下。

## 快速开始

依赖：**ffmpeg/ffprobe** 在 PATH（[官网下载](https://ffmpeg.org/download.html) 或 `winget install Gyan.FFmpeg`）；`Pillow + numpy` 可选（只影响自动验收对比图）。

```bash
python scripts/upscale2k.py 源视频.mp4           # 输出 源视频_2k.mp4
python scripts/upscale2k.py 源视频.mp4 输出.mp4  # 指定输出
```

脚本会自动：探源 → 跑链 → 完整性校验（时长对齐 / 音轨起点）→ 生成同帧 1:1 前后对比图 + 边缘能量比报告。

## 修复什么

✅ **任意视频通用**。三类典型病灶正面解决：黑底/渐变**色带**（deband）、压缩糊掉的**小字与边缘**（lanczos+CAS）、压缩**噪点**（hqdn3d）。

按内容类型可选微调（见 SKILL.md 表格）：实拍素材介意颗粒可把 hqdn3d 减量；追求毛孔级纹理极致重建可再叠加 AI 超分（RealESRGAN 等）作为可选进阶——本链是通用基底，先跑它看效果再说。

## 🔴 三条硬坑（每条都实撞过，写进脚本自动规避）

1. **`lanczos` 不是独立 ffmpeg 滤镜**——必须写 `scale=2560:1440:flags=lanczos`，写 `lanczos=2560:1440` 直接 Invalid argument。
2. **mp4 的 moov 索引转码结束才写入**——跑一半打开输出必报 "Invalid data / 无法打开"，不是坏了，等跑完。
3. **二手转码版不可作源**——QQ/微信转码会抽帧（实测 4842→4830 帧）+时间戳损伤，拿它的视频轨配原版音轨 = 音画错位（前几秒没声）。错位排查命令见 SKILL.md。

## 作为 Agent Skill 使用

仓库自带 Agent Skill 封装（`skills/`、`.claude/skills/`、`.agents/skills/`、`.opencode/skills/` 四份同内容），Claude Code / OpenCode / Qoder 等支持 skills 的环境可直接安装，对话里说"帮我补分辨率/升 2K"即可触发。

## 参数微调

| 症状 | 调整 |
|---|---|
| 小字过锐、白边 | `cas=0.6` → `0.4` |
| 黑底色带残留 | deband 已在链首，可再叠一次或调其阈值 |
| 压缩噪点重 | `hqdn3d=1.5:1.5:6:6` 前两位升到 2 |

## 验收口径（建议跑完自查）

- 同帧 1:1 像素对比（脚本自动生成 `*.cmp_old.jpg` / `*.cmp_new.jpg`）：边缘能量比（新/旧）**1.05~1.15** 为正常增益；低于 1.0 = 链子起反作用。
- 音轨：`ffprobe` 音频流 `start_time=0`，开头 3 秒 volumedetect 有响度。

## License

MIT

## English

**video-upscale-cpu** — resolution boost & restoration for ANY video: motion graphics, 2D/3D animation, live action, screen recordings, film clips. Pure-CPU ffmpeg chain: `deband` (kill dark-area banding) → `hqdn3d` (denoise) → `lanczos` upscale to 2560×1440 → `CAS 0.6` (sharpen text and edges). x264 crf15, audio untouched. Zero VRAM, no AI, no sign-up — a 161s clip finishes in minutes.

```bash
python scripts/upscale2k.py input.mp4            # → input_2k.mp4
python scripts/upscale2k.py input.mp4 output.mp4 # custom output
```

Requires ffmpeg/ffprobe on PATH; Pillow + numpy optional (auto before/after comparison report).

For per-content parameter tuning, verification workflow and three hard-won pitfalls (lanczos syntax, moov atom timing, IM-transcoded sources breaking A/V sync), see the SKILL.md and Chinese guide above.
