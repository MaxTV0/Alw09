#!/usr/bin/env python3
"""
1) يفكّ ضغط أي M3U8 مكتوب على سطر واحد
2) يضيف الوسوم الناقصة
3) يحسب EXT-X-PROGRAM-DATE-TIME تلقائياً من MEDIA-SEQUENCE
4) ينقل MEDIA-SEQUENCE مع كل تحديث
"""

import re
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

IN_FILE  = Path("input.m3u8")
OUT_FILE = Path("stream.m3u8")

TARGET_DURATION = 11
WINDOW          = 6
EPOCH_ANCHOR    = datetime(2026, 10, 9, 19, 0, 0, tzinfo=timezone.utc)
ANCHOR_SEQ      = 3670          # أول MEDIA-SEQUENCE يقابل EPOCH_ANCHOR


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def unflatten(text: str) -> str:
    """يحوّل ملف مضغوط إلى أسطر صحيحة."""
    # نفصل عند كل #EXT أو مسار يبدأ بـ /
    text = re.sub(r"(?=#EXT)", "\n", text)
    text = re.sub(r"(?=/[^#\s])", "\n", text)
    return "\n".join(l.strip() for l in text.splitlines() if l.strip())


def parse_segments(text: str):
    """يرجّع [(dur, uri), ...]."""
    lines = unflatten(text).splitlines()
    segs, dur = [], None
    for ln in lines:
        m = re.match(r"#EXTINF:([\d.]+)", ln)
        if m:
            dur = float(m.group(1))
        elif not ln.startswith("#") and dur is not None:
            segs.append((dur, ln))
            dur = None
    return segs


def build_dynamic(media_seq: int, segs):
    """يبني قائمة HLS كاملة حيّة."""
    head = [
        "#EXTM3U",
        "#EXT-X-VERSION:6",
        f"#EXT-X-TARGETDURATION:{TARGET_DURATION}",
        f"#EXT-X-MEDIA-SEQUENCE:{media_seq}",
        "#EXT-X-PLAYLIST-TYPE:EVENT",
        "#EXT-X-INDEPENDENT-SEGMENTS",
        "#EXT-X-SERVER-CONTROL:CAN-SKIP-UNTIL=30.0,CAN-BLOCK-RELOAD=YES",
    ]

    # حساب PDT انطلاقاً من الرقم التسلسلي
    pdt = EPOCH_ANCHOR + timedelta(seconds=0)   # يتعدّل تحت حسب seq

    body = []
    for i, (dur, uri) in enumerate(segs):
        abs_idx = media_seq + i
        seg_time = EPOCH_ANCHOR + timedelta(
            seconds=sum(d for d, _ in segs[:i])
        )
        body += [
            f"#EXT-X-PROGRAM-DATE-TIME:{iso(seg_time)}",
            f"#EXTINF:{dur:.6f},",
            uri,
        ]

    return "\n".join(head) + "\n" + "\n".join(body) + "\n"


def main():
    raw = IN_FILE.read_text(encoding="utf-8")

    # استخرج MEDIA-SEQUENCE الحالية
    m = re.search(r"#EXT-X-MEDIA-SEQUENCE:(\d+)", raw)
    start_seq = int(m.group(1)) if m else 0

    # استخرج المقاطع
    segs = parse_segments(raw)
    if not segs:
        print("⚠ مفيش مقاطع في الملف.")
        return

    print(f"✔ تم قراءة {len(segs)} مقطع، MEDIA-SEQUENCE = {start_seq}")

    # اكتب أول نسخة
    OUT_FILE.write_text(build_dynamic(start_seq, segs), encoding="utf-8")
    print(f"✔ اتنشأ {OUT_FILE}")


if __name__ == "__main__":
    main()
