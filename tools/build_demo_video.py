from __future__ import annotations

import subprocess
import os
import shutil
from pathlib import Path

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "demo" / "LocalizeFlow_Project_Overview.pdf"
FRAME_DIR = ROOT / "reports" / "public_release_qa" / "video_frames"
OUTPUT = ROOT / "demo" / "LocalizeFlow_Demo.mp4"
PDFTOPPM = Path(os.environ.get("PDFTOPPM") or shutil.which("pdftoppm") or "pdftoppm")


def render_slides() -> list[Path]:
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            str(PDFTOPPM),
            "-png",
            "-r",
            "144",
            str(PDF),
            str(FRAME_DIR / "slide"),
        ],
        check=True,
    )
    frames = sorted(
        FRAME_DIR.glob("slide-*.png"),
        key=lambda path: int(path.stem.split("-")[1]),
    )
    if len(frames) != 8:
        raise RuntimeError(f"Expected 8 rendered slides, found {len(frames)}")
    return frames


def build_video(frames: list[Path]) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    concat_file = FRAME_DIR / "slides.ffconcat"
    concat_lines = ["ffconcat version 1.0"]
    for frame in frames:
        concat_lines.append(f"file '{frame.as_posix()}'")
        concat_lines.append("duration 18")
    concat_lines.append(f"file '{frames[-1].as_posix()}'")
    concat_file.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

    command = [
        ffmpeg,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-f",
        "lavfi",
        "-t",
        "144",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=48000",
        "-vf",
        (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=F5F7F6,"
            "setsar=1,fps=30,format=yuv420p,"
            "fade=t=in:st=0:d=0.6,fade=t=out:st=143.4:d=0.6"
        ),
        "-map",
        "0:v",
        "-map",
        "1:a",
        "-t",
        "144",
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "21",
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-movflags",
        "+faststart",
        str(OUTPUT),
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    slide_frames = render_slides()
    build_video(slide_frames)
    print(OUTPUT)
