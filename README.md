# Visual Semiotics and Language Ideologies in Kyrgyz Digital Media
### A Computational Audit of YouTube Children's Content

---

## Overview

This repository contains the data, code, and analysis for a cultural analytics study examining whether YouTube children's content recommended to Kyrgyz users differs systematically in its **visual aesthetics** across language groups — specifically comparing Kyrgyz-language, Russian-language, and other content.

This project extends prior algorithmic audit work (*Empire Amplifier*) which demonstrated that YouTube disproportionately recommends Russian-language content to Kyrgyz children even when they signal preferences for Kyrgyz-language content. Where that work focused on *which* content gets recommended, this project asks: **what does that content look like**, and what do those visual differences signal ideologically?

Ethnographic interviews and participant observation in Bishkek, Kyrgyzstan suggest that:
- Kyrgyz-language children's content (e.g., *Keremet Koch*) is perceived as "static," low-production-value, and associated with Soviet-era educational media
- Russian-language content is perceived as more dynamic, colorful, and professionally produced
- These aesthetic perceptions reinforce broader language ideologies in which Russian is associated with modernity and prestige, while Kyrgyz is increasingly domain-restricted to elder speech and traditional contexts

This study operationalizes those perceptions as measurable visual features and tests whether they hold up computationally across a labeled corpus of YouTube videos.

---

## Research Questions

1. **Action density**: Is there a measurable difference in frame-by-frame pixel change (a proxy for "how much is happening") between Kyrgyz-language and Russian-language children's content?
2. **Shot length**: Do Russian-language videos have shorter average shot lengths (more frequent scene cuts) than Kyrgyz-language videos?
3. **Color saturation and luminance**: Does Russian/international content show higher average color saturation and brightness than Kyrgyz-produced content?
4. **Vlogger aesthetics**: Do Russian-language videos more frequently deploy "vlogger" visual markers — floating text overlays, bright graphical elements — compared to Kyrgyz content?

---

## Data

### Source
The primary dataset (`data/raw/all_urls_labels.csv`) is a corpus of YouTube video URLs collected during a sock-puppet algorithmic audit of YouTube recommendations in Kyrgyzstan. Each row is a unique video. Videos were labeled by research assistants at a university in Bishkek for:

- **Language spoken**: Russian, Kyrgyz, English, unknown, or other
- **Apparent ethnicity of speakers/characters**: Slavic, Kyrgyz, other Central Asian, Caucasian, other, no people
- Additional flags for unreachable/deleted videos

### Column reference

| Column | Description |
|---|---|
| `url` | Full YouTube URL |
| `is_russian` | `t` if primary language is Russian |
| `is_kyrgyz_x` | `t` if primary language is Kyrgyz (language label) |
| `is_english` | `t` if primary language is English |
| `is_unknown` | `t` if language could not be determined |
| `is_unreachable_x` | `t` if video was unavailable at time of labeling |
| `is_no_language` | `t` if video contains no speech |
| `other_lang` | Free text for other languages (e.g., `kazakh`); also used for `deleted` |
| `is_slavic` | `t` if speakers/characters appear Slavic |
| `is_kyrgyz_y` | `t` if speakers/characters appear Kyrgyz (ethnicity label) |
| `is_other_central_asian` | `t` if speakers/characters appear from other Central Asian groups |
| `is_caucasian` | `t` if speakers/characters appear Caucasian |
| `is_other` | `t` if speakers/characters are other ethnicity |
| `is_no_people` | `t` if no human/character faces present |
| `is_unreachable_y` | `t` if video was unavailable at time of ethnicity labeling |

### Frames (not in this repository)
Extracted video frames are too large to store on GitHub. The full frame dataset is archived at [Zenodo/Dataverse — link TBD]. The `frames/` directory is listed in `.gitignore`. See **Step 2** below for how to regenerate frames locally from the URL list.

### Processed data
After running the pipeline, two derived datasets are created in `data/processed/`:
- `manifest.csv` — records which videos were successfully processed and how many frames were extracted
- `visual_features.csv` — one row per video with all computed visual metrics (mean saturation, mean luminance, action density, mean shot length, text overlay frequency)

---

## Repository Structure

```
kyrgyz-youtube-visual-audit/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── data/
│   ├── raw/
│   │   └── all_urls_labels.csv
│   ├── processed/
│   │   ├── manifest.csv
│   │   ├── visual_features.csv
│   │   └── scene_cuts.csv
│   └── samples/
│       └── README.md
│
├── frames/                              # LOCAL ONLY — not committed to git
│   ├── russian/VIDEO_ID/frame_XXXX.jpg
│   ├── kyrgyz/VIDEO_ID/frame_XXXX.jpg
│   └── ...
│
├── notebooks/
│   ├── 00_data_exploration.ipynb
│   ├── 03_statistical_analysis.ipynb
│   └── 04_visualization.ipynb
│
├── scripts/
│   ├── 01_extract_frames.py
│   ├── 02_analyze_frames.py
│   └── utils.py
│
├── results/
│   ├── figures/
│   └── tables/
│
├── paper/
│   ├── draft.md
│   └── references.bib
│
└── environment/
    ├── requirements.txt
    └── environment.yml
```

---

## Setup

### Prerequisites

You will need:
- Python 3.9+
- `ffmpeg` installed on your system
- `yt-dlp` (Python package)
- A stable internet connection for frame extraction

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/kyrgyz-youtube-visual-audit.git
cd kyrgyz-youtube-visual-audit
```

### 2. Create a Python environment

**Option A — pip:**
```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r environment/requirements.txt
```

**Option B — conda:**
```bash
conda env create -f environment/environment.yml
conda activate kyrgyz-audit
```

### 3. Install ffmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to your PATH.

---

## Pipeline: Step-by-Step

### Step 1 — Explore the data

Open and run `notebooks/00_data_exploration.ipynb`.

This notebook gives you an overview of the labeled dataset before you start downloading anything:
- Distribution of language labels (how many Russian, Kyrgyz, English videos?)
- How many videos are deleted or unreachable?
- Cross-tabulations of language vs. apparent ethnicity labels
- Which videos to prioritize for frame extraction

**No downloads required for this step.**

---

### Step 2 — Extract frames from YouTube videos

Run `scripts/01_extract_frames.py` to download and sample frames from the videos in your CSV. This script **does not save full video files** — it streams each video through `yt-dlp` and pipes directly into `ffmpeg`, which extracts frames at your specified rate.

```bash
python scripts/01_extract_frames.py \
  --csv data/raw/all_urls_labels.csv \
  --output frames/ \
  --fps 0.5 \
  --max 50
```

**Arguments:**

| Argument | Default | Description |
|---|---|---|
| `--csv` | required | Path to your labeled URL CSV |
| `--output` | `./frames` | Root directory where frames will be saved |
| `--fps` | `0.5` | Frames per second to extract (0.5 = one frame every 2 seconds) |
| `--max` | `50` | Maximum number of videos to process per language group |

**Output structure:**
```
frames/
├── russian/
│   └── QXglaxD5fag/
│       ├── frame_0001.jpg
│       ├── frame_0002.jpg
│       └── ...
├── kyrgyz/
│   └── zncjz5HuQmo/
│       └── ...
```

A `manifest.csv` is written to your output directory recording which videos were processed successfully and how many frames were extracted.

**Notes:**
- The script automatically skips rows where `is_unreachable_x = t`, `is_unreachable_y = t`, `is_no_language = t`, or `other_lang = deleted`
- Each video is limited to its first 5 minutes by default (edit `max_duration` in the script to change this)
- Videos are capped at 480p resolution to reduce bandwidth
- Expect roughly 1–3 minutes per video depending on your connection speed
- Processing 50 videos per language group (~150 videos total) takes approximately 3–5 hours

**Recommended fps settings by analysis goal:**

| Goal | Recommended fps | Frames per 5-min video |
|---|---|---|
| Color / saturation analysis | 0.5 | ~150 |
| Action density | 2.0 | ~600 |
| Shot cut detection | 4.0+ | ~1200 |
| All of the above | 2.0 (compromise) | ~600 |

---

### Step 3 — Compute visual features

Run `scripts/02_analyze_frames.py` to compute visual metrics from the extracted frames.

```bash
python scripts/02_analyze_frames.py \
  --frames frames/ \
  --manifest frames/manifest.csv \
  --output data/processed/
```

This script produces `data/processed/visual_features.csv` with the following metrics per video:

| Feature | Description | Method |
|---|---|---|
| `mean_saturation` | Average color saturation across all frames | HSV color space, S channel mean |
| `mean_luminance` | Average brightness across all frames | HSV color space, V channel mean |
| `saturation_std` | Variability in saturation | Standard deviation across frames |
| `action_density` | Average pixel-level change between consecutive frames | Frame differencing (absolute pixel delta) |
| `mean_shot_length_sec` | Average duration between scene cuts | PySceneDetect content detector |
| `cuts_per_minute` | Number of scene transitions per minute | Derived from shot boundaries |
| `text_overlay_freq` | Proportion of frames containing visible text | EasyOCR detection |
| `n_frames` | Total number of frames analyzed | — |
| `language` | Language group from label CSV | — |

---

### Step 4 — Statistical analysis

Open and run `notebooks/03_statistical_analysis.ipynb`.

This notebook performs the core comparisons between language groups:

- **Descriptive statistics** — means, medians, standard deviations for each visual feature by language group
- **Group comparisons** — Kruskal-Wallis tests (non-parametric, appropriate for non-normal distributions) comparing Russian vs. Kyrgyz vs. English groups on each visual feature
- **Post-hoc pairwise tests** — Mann-Whitney U tests with Bonferroni correction for pairwise language group comparisons
- **Effect sizes** — Cohen's d or rank-biserial correlation to report practical significance alongside p-values
- **Correlation analysis** — are the visual features correlated with one another? (e.g., do high-saturation videos also tend to have faster cuts?)

Results are saved to `results/tables/`.

---

### Step 5 — Visualization

Open and run `notebooks/04_visualization.ipynb`.

This notebook generates publication-ready figures for the paper:

- Boxplots of saturation, luminance, and action density by language group
- Distribution plots of shot length (cuts per minute) by language group
- Bar chart of text overlay frequency by language group
- Scatter plots for feature correlations
- Example frame grids showing high vs. low saturation, high vs. low action density videos (for qualitative illustration)

Figures are saved to `results/figures/` as both `.png` (for drafts) and `.pdf` (for submission).

---

## Connecting Results to Theory

The visual features computed here are designed to operationalize claims made in ethnographic interviews and the language ideology literature:

| Community claim | Operationalization |
|---|---|
| "Kyrgyz cartoons are static / boring" | Action density, cuts per minute |
| "Russian content is more colorful / professional" | Mean saturation, mean luminance |
| "Russian content has vlogger aesthetics" | Text overlay frequency |
| Soviet-era aesthetic associations | Visual similarity clustering across language groups (exploratory) |

Findings should be interpreted alongside the qualitative interview data, not in isolation. The goal is triangulation: do computational patterns confirm, complicate, or contradict what community members report?

---

## Limitations

- **YouTube ToS**: Frame extraction via `yt-dlp` may conflict with YouTube's terms of service. This is standard practice in algorithmic audit research and should be acknowledged in the paper's methods section. No content is redistributed.
- **Video availability**: Some videos in the corpus have been deleted since original data collection. The `is_unreachable` flags track known deletions, but additional videos may have become unavailable.
- **Sampling**: Extracting frames at fixed intervals may miss brief events (fast cuts, short text overlays). Higher fps improves coverage at the cost of storage and compute.
- **Animation vs. live action**: Color and action density metrics may behave differently for animated content vs. live-action vlogger content. Consider analyzing these subgroups separately.
- **Language label quality**: Language labels were applied by human annotators. Inter-rater reliability scores should be reported if available.
- **Causal inference**: This study is observational. Visual differences between language groups reflect the content available on the platform; they do not establish that visual aesthetics cause children's language preferences.

---

## Citation

If you use this code or data, please cite:

```
[Citation TBD — to be added upon publication]
```

The prior algorithmic audit paper this work extends:

```
[Empire Amplifier citation — redacted for review]
```

---

## Contributors

| Name | Role |
|---|---|
| [Your name] | [Your role] |
| Ashley | Ethnographic data, interview corpus, Kyrgyz language ideology context |
| Nel | Research design, network analysis conceptualization |

---

## License

Code is released under the MIT License. See `LICENSE` for details. Data is released under CC BY 4.0.
