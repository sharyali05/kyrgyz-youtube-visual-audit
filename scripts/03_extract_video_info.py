import os
import av
import cv2
import numpy as np
import json
import hashlib
import pandas as pd
from pathlib import Path
from datetime import datetime
from yt_dlp import YoutubeDL
from dvt_mod.annotate_mod import yield_video
from dvt_mod.annotate_mod import annotate_shots
import matplotlib.pyplot as plt
import dvt
import polars as pl
from PIL import Image
import io
import json


# ── Configuration ────────────────────────────────────────────────────────
DOWNLOAD_DIR = Path("data/videos")
RESULTS_FILE = Path("data/results.csv")
PROGRESS_FILE = Path("data/progress.json")


# ── Progress Tracking ────────────────────────────────────────────────────
def load_progress() -> set:
    """Load set of already-completed URLs."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_progress(completed: set):
    """Persist the set of completed URLs."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(list(completed), f)


def mark_complete(url: str, completed: set):
    """Mark a URL as done and save immediately."""
    completed.add(url)
    save_progress(completed)


# ── Downloading ──────────────────────────────────────────────────────────
def url_to_filename(url: str) -> Path:
    """Deterministic filename from URL (so re-downloads are skipped)."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    # Preserve extension if possible
    ext = url.split(".")[-1].split("?")[0]
    if ext not in ("mp4", "webm", "avi", "mkv"):
        ext = "mp4"
    return DOWNLOAD_DIR / f"{url_hash}.{ext}"


def download_video(url: str) -> Path:
    """Download video if not already on disk. Returns local path."""

    local_path = url_to_filename(url)

    if local_path.exists():
        print(f"  Already downloaded: {local_path.name}")
        return local_path

    print(f"  Downloading: {url[:80]}...")

    ydl_opts = {
        'outtmpl': str(local_path),
        'format': 'bestvideo[height<=720][ext=mp4]/best[ext=mp4]',
        'quiet': True,
        'no_warnings': True,
        'js_runtimes': {'deno': {}},
        'remote_components': {'ejs': 'github'},
        'cookiefile': 'youtube-cookies.txt',
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)



# ── Processing ───────────────────────────────────────────────────────────
def process_video(video_path: Path) -> dict:
    """
    Your heavy processing goes here.
    Returns a dict of features.
    """

    vid_info = {}

    meta = dvt.video_info(video_path)
    vid_info['meta'] = meta
        
    # get scene breaks
    output = annotate_shots(video_path, False)
    dt = pl.from_dict(output['scenes'])
    dt = dt.with_columns((pl.col("start") / meta['fps']).alias("start_time"))
    dt = dt.with_columns((pl.col("end") / meta['fps']).alias("end_time"))

    vid_info['scenes'] = dt.to_dicts()

    # get color info across frames
    hue_text = """cnom,start,end,mid
    red,0.000000,0.015625,0.007812
    orange,0.015625,0.109375,0.062500
    yellow,0.109375,0.203125,0.156250
    green,0.203125,0.453125,0.328125
    cyan,0.453125,0.546875,0.500000
    blue,0.546875,0.765625,0.656250
    violet,0.765625,0.953125,0.859375
    red,0.953125,1.000000,0.976562"""

    # Use io.StringIO to treat the string as a file
    hue = pd.read_csv(io.StringIO(hue_text))

    frame_info = {}

    for image, frame, timestamp in yield_video(video_path):
        if frame % 30 == 0:
            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float64)

            hsv[:, :, 0] = hsv[:, :, 0] / 179.0
            hsv[:, :, 1] = hsv[:, :, 1] / 255.0
            hsv[:, :, 2] = hsv[:, :, 2] / 255.0

            h = hsv[:, :, 0] 
            s = hsv[:, :, 1]
            v = hsv[:, :, 2] 

            hsv = hsv.reshape((-1, 3))
            chroma = s * v
            
            flat = np.stack([h.ravel(), s.ravel(), v.ravel()], axis=1)
            chromatic = flat[flat[:, 1] * flat[:, 2] > 0.3]

            if len(chromatic) > 0:
                bins = np.append(0, hue.end.values)
                cnt, _ = np.histogram(hsv[(hsv[:,1] * hsv[:,2] > 0.3), 0], bins = bins)
                cnt[0] = cnt[0] + cnt[7]
                cnt = cnt[:7]
                dom_color = hue.cnom.values[np.argmax(cnt)]
                color_percent = np.max(cnt) / hsv.shape[0] * 100
            else:
                dom_color = "achromatic"
                color_percent = 0.0

            features = {
                "avg_brightness": float(np.mean(v)),
                "avg_chroma":     float(np.mean(chroma)),
                "brightness_std": float(np.std(v)),
                "chroma_std":     float(np.std(chroma)),
                "dom_color" :     dom_color,
                "dom_color_percent":    color_percent
            }
            
            frame_info[frame] = features

        vid_info['frames'] = frame_info
    return vid_info

def cleanup(video_path: Path):
    """4. Deletes the file if it exists."""
    if os.path.exists(video_path):
        os.remove(video_path)
        print(f"Cleanup: Deleted {video_path}")


# ── Results Saving ───────────────────────────────────────────────────────
def save_result(url: str, features: dict):
    """Append one result row to the CSV."""
    row = {"url": url, **features}
   
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "a") as f:
            f.write(json.dumps(row, default=str) + "\n") 
    else:
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RESULTS_FILE, "a") as f:
            f.write(json.dumps(row, default=str) + "\n") 


# ── Main Pipeline ────────────────────────────────────────────────────────
def run_pipeline(input_csv: str):
    """
    Main entry point.
    Reads URLs from CSV, downloads, processes, saves results.
    Safe to restart — skips already-completed URLs.
    """
    urls_df = pd.read_csv(input_csv)
    urls_df = urls_df[urls_df['most_recommended_demographic'] == 'child']
    urls_df = urls_df[((urls_df['is_russian'] == 't') | (urls_df['is_kyrgyz_x'] == 't')) | (urls_df['is_english'] == 't')]
    urls = urls_df["url"].tolist()

    completed = load_progress()
    total = len(urls)
    skipped = sum(1 for u in urls if u in completed)
    print(f"Total: {total} | Already done: {skipped} | Remaining: {total - skipped}")
    print("=" * 60)

    for i, url in enumerate(urls):
        # ── Skip if already processed ──
        if url in completed:
            continue

        print(f"\n[{i+1}/{total}] {url[:80]}")

        try:
            # Download (skips if file exists)
            video_path = download_video(url)

            # Process
            print(f"  Processing...")
            features = process_video(video_path)

            # Save result
            save_result(url, features)
            print(f"  ✓ Done ")

            # Mark as complete (persists immediately)
            mark_complete(url, completed)

            cleanup(video_path)

        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            # Don't mark as complete — will retry on next run
            continue

    print("\n" + "=" * 60)
    print(f"Pipeline complete. Results in: {RESULTS_FILE}")


# ── Entry Point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline("../data/raw/all_urls_labels.csv")