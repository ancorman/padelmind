import os
import subprocess
import tempfile
from rally import RallyWindow

PADDING_SEC = 1.5   # seconds added before/after each rally
MAX_RALLIES = 6     # top N by duration


def cut(video_path: str, output_path: str, rallies: list[RallyWindow]) -> bool:
    """
    Cut and concatenate top rallies into a highlight reel.
    Returns True on success.
    """
    if not rallies:
        return False

    top = sorted(rallies, key=lambda r: r.duration_sec, reverse=True)[:MAX_RALLIES]
    top = sorted(top, key=lambda r: r.start_sec)  # chronological order

    with tempfile.TemporaryDirectory() as tmp:
        clip_paths: list[str] = []

        for i, rally in enumerate(top):
            start = max(0.0, rally.start_sec - PADDING_SEC)
            duration = rally.duration_sec + PADDING_SEC * 2
            clip = os.path.join(tmp, f"clip_{i:02d}.mp4")

            result = subprocess.run([
                "ffmpeg", "-y",
                "-ss", str(start),
                "-i", video_path,
                "-t", str(duration),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                clip,
            ], capture_output=True)

            if result.returncode == 0:
                clip_paths.append(clip)

        if not clip_paths:
            return False

        # Concatenate clips
        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w") as f:
            for cp in clip_paths:
                f.write(f"file '{cp}'\n")

        result = subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output_path,
        ], capture_output=True)

        return result.returncode == 0
