#!/usr/bin/env python3
"""
مولّد M3U8 أساسي — يخفي المصدر ويولّد قائمة نظيفة
"""
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ⚠️ غيّر ده لدومين الـ Worker بتاعك
WORKER_URL = "https://alw09.alhndyalsyrfr19.workers.dev"
OUT_FILE   = Path("stream.m3u8")
SEG_DUR    = 10.0
WINDOW     = 6
TARGET_DUR = 11

def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"

def build(media_seq, epoch):
    lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:6",
        f"#EXT-X-TARGETDURATION:{TARGET_DUR}",
        f"#EXT-X-MEDIA-SEQUENCE:{media_seq}",
        "#EXT-X-PLAYLIST-TYPE:EVENT",
        "#EXT-X-INDEPENDENT-SEGMENTS",
    ]
    for i in range(WINDOW):
        idx = media_seq + i
        pdt = epoch + timedelta(seconds=SEG_DUR * idx)
        lines.append(f"#EXT-X-PROGRAM-DATE-TIME:{iso(pdt)}")
        lines.append(f"#EXTINF:{SEG_DUR:.3f},")
        lines.append(f"{WORKER_URL}/segment.ts")
    return "\n".join(lines) + "\n"

def main():
    epoch = datetime.now(timezone.utc).replace(microsecond=0)
    OUT_FILE.write_text(build(0, epoch), encoding="utf-8")
    print(f"✔ تم توليد {OUT_FILE}")

if __name__ == "__main__":
    main()
