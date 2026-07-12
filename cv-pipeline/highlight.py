import json
import os
import subprocess
import tempfile
from rally import RallyWindow

PADDING_SEC = 1.5    # seconds added before/after each rally
MAX_RALLIES = 6      # top N to include
MAX_MB = 15          # WhatsApp-friendly ceiling
VERTICAL = True      # 9:16 (1080x1920) for WhatsApp/IG


def _duration(path: str) -> float:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def _select(rallies: list[RallyWindow], n: int) -> list[RallyWindow]:
    """Pick the most highlight-worthy rallies — long AND intense beats just long.
    Falls back to duration-only when intensity is unavailable (old windows)."""
    def score(r: RallyWindow) -> float:
        inten = getattr(r, "intensity", 0.0) or 0.0
        return r.duration_sec * (0.5 + inten)     # intensity scales duration
    top = sorted(rallies, key=score, reverse=True)[:n]
    return sorted(top, key=lambda r: r.start_sec)  # chronological in the reel


# 9:16 with a blurred zoom-fill background so the whole (wide) court stays visible
# instead of being cropped away. This is the polished reel look.
_VFILTER = (
    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
    "crop=1080:1920,boxblur=22:2[bg];"
    "[0:v]scale=1080:-2:force_original_aspect_ratio=decrease[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]"
)


def cut(video_path: str, output_path: str, rallies: list[RallyWindow],
        vertical: bool = VERTICAL, max_mb: int = MAX_MB) -> bool:
    """Cut top rallies into one reel. Vertical 9:16 blur-fill, capped at max_mb."""
    if not rallies:
        return False
    top = _select(rallies, MAX_RALLIES)

    with tempfile.TemporaryDirectory() as tmp:
        clips: list[str] = []
        for i, r in enumerate(top):
            start = max(0.0, r.start_sec - PADDING_SEC)
            duration = r.duration_sec + PADDING_SEC * 2
            clip = os.path.join(tmp, f"clip_{i:02d}.mp4")
            cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", video_path, "-t", str(duration)]
            if vertical:
                cmd += ["-filter_complex", _VFILTER, "-map", "[v]", "-map", "0:a?"]
            cmd += ["-c:v", "libx264", "-preset", "fast", "-crf", "25",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", clip]
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                clips.append(clip)

        if not clips:
            return False

        # All clips share format now → concat copy is safe
        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w") as f:
            for cp in clips:
                f.write(f"file '{cp}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", output_path],
            capture_output=True,
        )
        if not os.path.exists(output_path):
            return False

        # Enforce the size ceiling — re-encode to a computed bitrate if over
        if os.path.getsize(output_path) > max_mb * 1_000_000:
            dur = _duration(output_path) or 30.0
            budget_kbps = (max_mb * 8 * 1000) / dur          # total budget
            v_kbps = max(700, int(budget_kbps * 0.90) - 96)  # leave room for audio + overhead
            tmp_out = output_path + ".fit.mp4"
            subprocess.run(
                ["ffmpeg", "-y", "-i", output_path, "-c:v", "libx264", "-preset", "fast",
                 "-b:v", f"{v_kbps}k", "-maxrate", f"{int(v_kbps * 1.3)}k", "-bufsize", f"{v_kbps * 2}k",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", tmp_out],
                capture_output=True,
            )
            if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 0:
                os.replace(tmp_out, output_path)

        return os.path.getsize(output_path) > 0
