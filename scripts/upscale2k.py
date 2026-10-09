#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""动效图视频补分辨率（纯 CPU 链）——deband→hqdn3d→lanczos 2K→CAS。
用法: python upscale2k.py <源视频> [输出路径]
依赖: ffmpeg/ffprobe 在 PATH；Pillow+numpy 仅用于验收对比图。
"""
import os, sys, json, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def sh(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)

def probe(path):
    r = sh(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
            "stream=width,height,nb_frames:format=duration","-of","json",path])
    return json.loads(r.stdout or "{}")

def main():
    if len(sys.argv) < 2:
        print("用法: python upscale2k.py <源视频> [输出路径]"); sys.exit(1)
    src = os.path.abspath(sys.argv[1])
    if not os.path.isfile(src):
        print("源文件不存在:", src); sys.exit(1)
    out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else \
          os.path.splitext(src)[0] + "_2k.mp4"
    if os.path.abspath(out) == src:
        print("输出路径不能与源相同"); sys.exit(1)

    info = probe(src)
    vs = (info.get("streams") or [{}])[0]
    w, h = int(vs.get("width",0)), int(vs.get("height",0))
    dur = float(info.get("format",{}).get("duration",0) or 0)
    print("源: %dx%d, %.1fs" % (w, h, dur))
    if h >= 1440:
        print("源已经 ≥1440p，只做修复不放大（deband+轻锐化）。")
        vf = "deband,hqdn3d=1.5:1.5:6:6,cas=0.4"
    else:
        tw, th = 2560, 1440
        vf = "deband,hqdn3d=1.5:1.5:6:6,scale=%d:%d:flags=lanczos,cas=0.6" % (tw, th)
        print("目标: %dx%d" % (tw, th))
    print("⚠️ 确认源是原始版而非 QQ/微信二手转码（二手源音画必错位）。开始跑，完成后才生成 mp4 索引，中途打不开属正常。")
    sys.stdout.flush()

    r = sh(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",src,
            "-vf",vf,"-c:v","libx264","-crf","15","-preset","medium","-c:a","copy",out])
    if r.returncode != 0:
        print("ffmpeg 失败:\n"+r.stderr[-800:]); sys.exit(1)

    o = probe(out)
    oh = int((o.get("streams") or [{}])[0].get("height",0))
    odur = float(o.get("format",{}).get("duration",0) or 0)
    print("输出: %dx%d, %.1fs, %.1fMB" % (o.get("streams",[{}])[0].get("width",0), oh, odur,
                                          os.path.getsize(out)/1048576))
    if abs(odur-dur) > max(0.5, dur*0.005):
        print("⚠️ 时长偏差 %.2fs，检查音轨。" % abs(odur-dur))
    a = sh(["ffprobe","-v","error","-select_streams","a:0","-show_entries",
            "stream=start_time","-of","csv=p=0",out])
    if a.stdout.strip() and a.stdout.strip() not in ("0.000000","N/A"):
        print("⚠️ 音轨起点非 0（%s），可能音画错位。" % a.stdout.strip())

    # 验收对比图：取 60% 处一帧，旧版 nearest 对齐 vs 新版裁同区
    try:
        import numpy as np
        from PIL import Image
        ts = str(round(dur*0.6, 2))
        f_old = out + ".cmp_old.jpg"; f_new = out + ".cmp_new.jpg"
        cw, ch = 960, 540
        x0, y0 = (w-cw)//2, (h-ch)//2
        sh(["ffmpeg","-y","-loglevel","error","-ss",ts,"-i",src,"-frames:v","1",
            "-vf","crop=%d:%d:%d:%d,scale=%d:%d:flags=neighbor"%(cw,ch,x0,y0,cw*2,ch*2),f_old])
        sh(["ffmpeg","-y","-loglevel","error","-ss",ts,"-i",out,"-frames:v","1",
            "-vf","crop=%d:%d:%d:%d"%(cw*2,ch*2,x0*2,y0*2),f_new])
        a = np.asarray(Image.open(f_old).convert("L"), dtype=np.float32)
        b = np.asarray(Image.open(f_new).convert("L"), dtype=np.float32)
        ga_y, ga_x = np.gradient(a); gb_y, gb_x = np.gradient(b)
        va = float((ga_x**2+ga_y**2).mean()); vb = float((gb_x**2+gb_y**2).mean())
        print("同帧对比图: %s / %s" % (f_old, f_new))
        print("边缘能量 old=%.0f new=%.0f 比值=%.2f（1.05~1.15 为正常增益）" % (va, vb, vb/max(va,1)))
        print("⚠️ 对比图必须自己打开看：小字边缘 + 黑底色带两个观察点。")
    except Exception as e:
        print("对比图生成失败（不影响成片）:", e)

if __name__ == "__main__":
    main()
