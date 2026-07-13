#!/usr/bin/env python3
"""Collapse YouTube auto-caption VTT files into clean plain text.

Auto-subs repeat each line many times as the caption rolls; this strips cues,
tags, and the rolling duplicates so the transcript reads as prose we can mine
for coaching cues.

Usage:  python vtt_to_text.py transcripts/  ->  writes transcripts/text/<id>.txt
"""
import sys
import os
import re
import glob

TAG = re.compile(r"<[^>]+>")
TIMING = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->")


def clean(vtt_path):
    lines = []
    for raw in open(vtt_path, encoding="utf-8", errors="ignore"):
        s = raw.rstrip("\n")
        if (not s or s.startswith(("WEBVTT", "Kind:", "Language:"))
                or TIMING.match(s) or s.strip().isdigit()):
            continue
        s = TAG.sub("", s).replace("&nbsp;", " ").strip()
        if not s:
            continue
        lines.append(s)
    # collapse consecutive duplicates (the rolling-caption repeat)
    out = []
    for s in lines:
        if not out or out[-1] != s:
            out.append(s)
    # second pass: drop a line if it's fully contained in the previous joined tail
    text, seen_tail = [], ""
    for s in out:
        if s and s not in seen_tail:
            text.append(s)
            seen_tail = (seen_tail + " " + s)[-400:]
    return " ".join(text)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "transcripts"
    outdir = os.path.join(src, "text")
    os.makedirs(outdir, exist_ok=True)
    n = 0
    for vtt in glob.glob(os.path.join(src, "*.vtt")):
        base = os.path.basename(vtt)
        vid = base.split("|", 1)[0]
        title = base.split("|", 1)[-1].rsplit(".", 2)[0] if "|" in base else base
        txt = clean(vtt)
        with open(os.path.join(outdir, vid + ".txt"), "w", encoding="utf-8") as f:
            f.write(f"# {title}\n# video_id: {vid}\n\n{txt}\n")
        n += 1
    print(f"cleaned {n} transcripts -> {outdir}")


if __name__ == "__main__":
    main()
