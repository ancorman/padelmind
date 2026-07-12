#!/usr/bin/env python3
"""
Ingest a video from a YouTube (or other yt-dlp-supported) URL into PadelMind.

Downloads to the shared videos dir so the CV pipeline / pose_label_gen / highlight
cutter can use it. Optionally grabs just a time segment (great for testing —
don't pull a whole 40-min match when 90s will do).

Usage:
  python3 fetch_youtube.py <url> [out_name] [--section START-END]
Examples:
  python3 fetch_youtube.py "https://youtu.be/XXXX" test_clip
  python3 fetch_youtube.py "https://youtu.be/XXXX" fh_demo --section 00:30-02:00
"""

import os
import subprocess
import sys

# Prefer the venv/system yt-dlp; fall back to python -m yt_dlp
YTDLP_CANDIDATES = [
    "yt-dlp",
    "/Library/Frameworks/Python.framework/Versions/3.14/bin/yt-dlp",
    os.path.expanduser("~/Library/Python/3.11/bin/yt-dlp"),
]

DEFAULT_DIR = os.environ.get("PADEL_VIDEO_DIR", "/Volumes/AXMedia/PadelMind/cv-data/videos")


def _ytdlp():
    for c in YTDLP_CANDIDATES:
        if c == "yt-dlp" or os.path.exists(c):
            if subprocess.run(["bash", "-lc", f"command -v {c} || test -x {c}"],
                              capture_output=True).returncode == 0 or os.path.exists(c):
                return c
    return "yt-dlp"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    url = sys.argv[1]
    out_name = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "yt_clip"
    section = None
    if "--section" in sys.argv:
        section = sys.argv[sys.argv.index("--section") + 1]

    if not os.path.isdir(DEFAULT_DIR):
        sys.exit(f"Video dir not found (external drive mounted?): {DEFAULT_DIR}")

    out_path = os.path.join(DEFAULT_DIR, f"{out_name}.%(ext)s")
    cmd = [_ytdlp(), "--no-playlist",
           "-f", "best[height<=1080][ext=mp4]/best[height<=1080]/best",
           "-o", out_path]
    if section:
        cmd += ["--download-sections", f"*{section}"]
    cmd.append(url)

    print(f"Fetching {url}" + (f" [{section}]" if section else "") + f" -> {DEFAULT_DIR}/{out_name}.mp4")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(f"yt-dlp failed (code {r.returncode})")

    final = os.path.join(DEFAULT_DIR, f"{out_name}.mp4")
    if os.path.exists(final):
        size = os.path.getsize(final) / 1e6
        print(f"Saved {final}  ({size:.0f} MB)")
        print("Next: pose_label_gen.py / handler.py / highlight.py can now use this path.")
    else:
        print("Download finished (check the videos dir for the file).")


if __name__ == "__main__":
    main()
