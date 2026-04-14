"""
Frame Extraction Pipeline for YouTube Video Analysis
=====================================================
Takes a CSV of YouTube URLs with language labels and extracts sampled frames
without storing full video files. Frames are saved organized by video ID.

Requirements:
    pip install yt-dlp pandas
    conda install ffmpeg   # already included if using environment.yml

Usage:
    python scripts/01_extract_frames.py \
        --csv data/raw/all_urls_labels.csv \
        --output frames/ \
        --fps 0.5 \
        --max 50
"""

import re
import subprocess
import argparse
import pandas as pd
from pathlib import Path


def get_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    match = re.search(r"v=([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None


def is_valid_row(row) -> bool:
    """Skip deleted, unreachable, or no-language rows."""
    skip_flags = ["is_unreachable_x", "is_unreachable_y", "is_no_language"]
    for flag in skip_flags:
        if flag in row.index and row[flag] == "t":
            return False
    if "other_lang" in row.index and row["other_lang"] == "deleted":
        return False
    return True


def get_language_label(row) -> str:
    """Return a simple language string for folder organization."""
    if row.get("is_russian") == "t":
        return "russian"
    elif row.get("is_kyrgyz_x") == "t" or row.get("is_kyrgyz_y") == "t":
        return "kyrgyz"
    elif row.get("is_english") == "t":
        return "english"
    else:
        return "other"


def extract_frames(url: str, output_dir: Path, fps: float = 0.5, max_duration: int = 300):
    """
    Stream a YouTube video via yt-dlp and pipe directly to ffmpeg for frame extraction.
    No full video file is stored on disk.

    Args:
        url:          YouTube video URL
        output_dir:   Directory to save frames for this video
        fps:          Frames per second to extract (0.5 = one frame every 2 seconds)
        max_duration: Stop after this many seconds (default: first 5 minutes)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_pattern = str(output_dir / "frame_%04d.jpg")

    ydl_cmd = [
        "yt-dlp",
        "--quiet",
        "--no-warnings",
        "-f", "best[height<=480]",  # cap at 480p to reduce bandwidth
        "-o", "-",                   # stream to stdout
        url
    ]

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", "pipe:0",             # read from stdin
        "-t", str(max_duration),    # only first N seconds
        "-vf", f"fps={fps}",        # sample rate
        "-q:v", "2",                # JPEG quality (2 = high)
        "-y",                       # overwrite without asking
        frame_pattern
    ]

    try:
        ydl_proc = subprocess.Popen(
            ydl_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ffmpeg_cmd,
            stdin=ydl_proc.stdout,
            capture_output=True,
            timeout=120             # kill if over 2 minutes
        )
        ydl_proc.wait()

        n_frames = len(list(output_dir.glob("*.jpg")))
        return n_frames

    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {url}")
        return 0
    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return 0


def run_pipeline(csv_path: str, output_root: str, fps: float, max_per_language: int):
    """
    Main pipeline: read CSV, filter valid rows, extract frames organized by language.

    Args:
        csv_path:         Path to your labels CSV
        output_root:      Root directory for all extracted frames
        fps:              Frames per second to sample
        max_per_language: Cap on videos per language group
    """
    df = pd.read_csv(csv_path)  # comma-separated CSV
    output_root = Path(output_root)

    counts = {"russian": 0, "kyrgyz": 0, "english": 0, "other": 0}
    results = []

    for _, row in df.iterrows():
        if not is_valid_row(row):
            continue

        url = row["url"]
        video_id = get_video_id(url)
        if not video_id:
            continue

        lang = get_language_label(row)

        if counts[lang] >= max_per_language:
            continue

        print(f"[{lang.upper()}] Processing {video_id} ({counts[lang]+1}/{max_per_language})")

        video_output_dir = output_root / lang / video_id
        n_frames = extract_frames(url, video_output_dir, fps=fps)

        counts[lang] += 1
        results.append({
            "video_id":           video_id,
            "url":                url,
            "language":           lang,
            "n_frames_extracted": n_frames,
            "frame_dir":          str(video_output_dir)
        })
        print(f"  → {n_frames} frames saved to {video_output_dir}")

    manifest = pd.DataFrame(results)
    manifest_path = output_root / "manifest.csv"
    manifest.to_csv(manifest_path, index=False)
    print(f"\nDone. Manifest saved to {manifest_path}")
    print(f"Totals: {counts}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract frames from YouTube URLs in a labeled CSV."
    )
    parser.add_argument("--csv",    required=True,           help="Path to labeled URL CSV")
    parser.add_argument("--output", default="./frames",      help="Root output directory for frames")
    parser.add_argument("--fps",    type=float, default=0.5, help="Frames per second to extract")
    parser.add_argument("--max",    type=int,   default=50,  help="Max videos per language group")
    args = parser.parse_args()

    run_pipeline(args.csv, args.output, args.fps, args.max)
