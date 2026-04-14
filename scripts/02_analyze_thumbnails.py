"""
Thumbnail-Based Visual Feature Extraction
==========================================
Instead of downloading full videos, this script fetches YouTube thumbnails
(tiny image files) and computes visual features from them directly.

This is much faster than frame extraction — thousands of videos per minute
instead of 1-2 videos per minute.

Features computed per video:
    - mean_saturation:    Average color saturation (HSV S channel)
    - mean_luminance:     Average brightness (HSV V channel)
    - saturation_std:     Variability in saturation
    - luminance_std:      Variability in brightness
    - mean_hue:           Dominant hue (HSV H channel)
    - red_ratio:          Proportion of pixels that are red/orange
    - blue_ratio:         Proportion of pixels that are blue
    - text_overlay:       Whether EasyOCR detects text in the thumbnail (1/0)
    - n_text_chars:       Number of characters detected by OCR
    - thumbnail_found:    Whether a thumbnail was successfully fetched (1/0)

Requirements:
    pip install pandas numpy opencv-python requests tqdm easyocr Pillow

Usage:
    python scripts/02_analyze_thumbnails.py \
        --csv data/raw/all_urls_labels.csv \
        --output data/processed/visual_features.csv \
        --max 200 \
        --ocr
"""

import re
import argparse
import requests
import numpy as np
import pandas as pd
import cv2
from pathlib import Path
from io import BytesIO
from PIL import Image
from tqdm import tqdm


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_video_id(url: str) -> str:
    """Extract YouTube video ID from a URL."""
    match = re.search(r"v=([a-zA-Z0-9_-]{11})", str(url))
    return match.group(1) if match else None


def get_thumbnail_url(video_id: str) -> list:
    """Return thumbnail URLs in order of preference (highest quality first)."""
    return [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/default.jpg",
    ]


def fetch_thumbnail(video_id: str, timeout: int = 10):
    """
    Fetch the best available thumbnail for a video.
    Returns a numpy BGR image array, or None if all attempts fail.
    """
    for url in get_thumbnail_url(video_id):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content)).convert("RGB")
                img_array = np.array(img)
                # YouTube returns a small grey placeholder for missing thumbnails
                # Detect it by checking if image is very small or nearly uniform grey
                if img_array.shape[0] < 90:
                    continue
                return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        except Exception:
            continue
    return None


def is_valid_row(row) -> bool:
    """Skip deleted, unreachable, or no-language rows."""
    for flag in ["is_unreachable_x", "is_unreachable_y", "is_no_language"]:
        if flag in row.index and row[flag] == "t":
            return False
    if "other_lang" in row.index and row["other_lang"] == "deleted":
        return False
    return True


def get_language_label(row) -> str:
    """Assign a single language label per row."""
    if row.get("is_russian") == "t":    return "russian"
    elif row.get("is_kyrgyz_x") == "t": return "kyrgyz"
    elif row.get("is_english") == "t":  return "english"
    else:                               return "other"


# ── Visual feature extraction ────────────────────────────────────────────────

def extract_color_features(bgr_img: np.ndarray) -> dict:
    """
    Compute color-based visual features from a BGR image.

    Returns a dict with saturation, luminance, hue, and color ratio features.
    All values are on a 0-255 scale unless noted.
    """
    hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    # ── Basic HSV stats ───────────────────────────────────────────────────────
    features = {
        "mean_saturation": float(np.mean(s)),
        "mean_luminance":  float(np.mean(v)),
        "saturation_std":  float(np.std(s)),
        "luminance_std":   float(np.std(v)),
        "mean_hue":        float(np.mean(h)),
    }

    # ── Color ratios ──────────────────────────────────────────────────────────
    # Red/orange pixels: hue 0-15 or 160-180 (wraps around in HSV)
    red_mask = ((h <= 15) | (h >= 160)) & (s > 50)
    features["red_ratio"] = float(np.mean(red_mask))

    # Blue pixels: hue 100-130
    blue_mask = (h >= 100) & (h <= 130) & (s > 50)
    features["blue_ratio"] = float(np.mean(blue_mask))

    # Yellow pixels: hue 20-35 (McDonald's effect — attention-grabbing)
    yellow_mask = (h >= 20) & (h <= 35) & (s > 80)
    features["yellow_ratio"] = float(np.mean(yellow_mask))

    return features


def extract_ocr_features(bgr_img: np.ndarray, reader) -> dict:
    """
    Use EasyOCR to detect text overlays in the image.
    Returns whether text was found and total character count.
    """
    try:
        rgb_img = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)
        results = reader.readtext(rgb_img, detail=0)
        text = " ".join(results)
        return {
            "text_overlay": 1 if len(text.strip()) > 0 else 0,
            "n_text_chars": len(text.strip())
        }
    except Exception:
        return {"text_overlay": 0, "n_text_chars": 0}


# ── Main pipeline ────────────────────────────────────────────────────────────

def run_pipeline(csv_path: str, output_path: str, max_per_language: int, use_ocr: bool):
    """
    Main pipeline: fetch thumbnails and extract visual features for each video.

    Args:
        csv_path:         Path to labeled URL CSV
        output_path:      Path to save visual_features.csv
        max_per_language: Max videos to process per language group
        use_ocr:          Whether to run EasyOCR text detection (slower)
    """
    df = pd.read_csv(csv_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Optionally load EasyOCR ───────────────────────────────────────────────
    reader = None
    if use_ocr:
        print("Loading EasyOCR model (first run downloads ~100MB)...")
        import easyocr
        reader = easyocr.Reader(["en", "ru"], gpu=False)
        print("EasyOCR ready.")

    counts  = {"russian": 0, "kyrgyz": 0, "english": 0, "other": 0}
    results = []

    # Filter to valid rows only
    valid_rows = [row for _, row in df.iterrows() if is_valid_row(row)]
    print(f"Valid rows to process: {len(valid_rows):,}")

    for row in tqdm(valid_rows, desc="Processing videos"):
        url      = row["url"]
        video_id = get_video_id(url)
        if not video_id:
            continue

        lang = get_language_label(row)
        if counts[lang] >= max_per_language:
            continue

        # ── Fetch thumbnail ───────────────────────────────────────────────────
        img = fetch_thumbnail(video_id)

        record = {
            "video_id":        video_id,
            "url":             url,
            "language":        lang,
            "thumbnail_found": 1 if img is not None else 0,
        }

        if img is not None:
            record.update(extract_color_features(img))
            if use_ocr and reader is not None:
                record.update(extract_ocr_features(img, reader))
            else:
                record.update({"text_overlay": None, "n_text_chars": None})
        else:
            # Fill with NaN if thumbnail not found
            for col in ["mean_saturation", "mean_luminance", "saturation_std",
                        "luminance_std", "mean_hue", "red_ratio", "blue_ratio",
                        "yellow_ratio", "text_overlay", "n_text_chars"]:
                record[col] = None

        counts[lang] += 1
        results.append(record)

    # ── Save results ──────────────────────────────────────────────────────────
    features_df = pd.DataFrame(results)
    features_df.to_csv(output_path, index=False)

    print(f"\nDone! Visual features saved to {output_path}")
    print(f"Videos processed per language group: {counts}")
    print(f"\nSuccess rate (thumbnail found):")
    for lang in ["russian", "kyrgyz", "english", "other"]:
        subset = features_df[features_df["language"] == lang]
        if len(subset) > 0:
            pct = subset["thumbnail_found"].mean() * 100
            print(f"  {lang:<12} {pct:.1f}% ({subset['thumbnail_found'].sum()}/{len(subset)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract visual features from YouTube thumbnails."
    )
    parser.add_argument("--csv",    required=True,
                        help="Path to labeled URL CSV")
    parser.add_argument("--output", default="data/processed/visual_features.csv",
                        help="Path to save output CSV")
    parser.add_argument("--max",    type=int, default=200,
                        help="Max videos per language group (default: 200)")
    parser.add_argument("--ocr",    action="store_true",
                        help="Run EasyOCR text detection on thumbnails (slower)")
    args = parser.parse_args()

    run_pipeline(args.csv, args.output, args.max, args.ocr)
