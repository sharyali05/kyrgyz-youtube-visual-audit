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

This study operationalizes those perceptions as measurable visual features extracted from **YouTube thumbnails** and tests whether they hold up computationally across a labeled corpus of YouTube videos. Thumbnails are used instead of full video frames because they are lightweight, fast to retrieve, and designed by creators to be visually representative of their content — making them valid proxies for color, brightness, and vlogger aesthetic features.

---

## Key Findings

| Feature | Direction | Effect size | Significant |
|---|---|---|---|
| Luminance (brightness) | Russian > Kyrgyz | Medium (r = 0.36) | ✓ Yes (p < 0.05) |
| Text overlay density | Russian > Kyrgyz | Small (r = 0.11) | ✗ p = 0.064 |
| Color saturation | Russian > Kyrgyz | Small (r = 0.19) | ✗ |
| Blue pixel ratio | Kyrgyz > Russian | Small (r = 0.16) | ✗ |

Russian-language thumbnails are significantly brighter than Kyrgyz-language thumbnails (median luminance 156.7 vs. 127.3 on a 0–255 scale). Russian and English thumbnails also show higher text overlay rates than Kyrgyz thumbnails (19.8% and 20.8% vs. 13.2%), consistent with the commercial vlogger aesthetic described by community members in ethnographic interviews. Unexpectedly, Kyrgyz thumbnails show higher blue pixel ratios than Russian ones, suggesting a distinct rather than simply deficient visual register.

---

## Research Questions

1. **Luminance**: Does Russian/international content show higher average brightness than Kyrgyz-produced content?
2. **Color saturation**: Does Russian/international content show higher average color saturation than Kyrgyz-produced content?
3. **Vlogger aesthetics**: Do Russian-language videos more frequently deploy "vlogger" visual markers — floating text overlays, bright graphical elements — compared to Kyrgyz content?
4. **Color composition**: Do Kyrgyz and Russian-language videos differ in their dominant color profiles (hue, red/yellow/blue ratios)?

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

### Processed data
Two derived datasets are available in `data/processed/`:

- `visual_features.csv` — one row per video with color and luminance metrics
- `visual_features_with_text.csv` — extends the above with text overlay detection metrics

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
│   │   └── all_urls_labels.csv              # Labeled URL corpus
│   ├── processed/
│   │   ├── visual_features.csv              # Color/luminance features per video
│   │   └── visual_features_with_text.csv    # + text overlay features
│
├── notebooks/
│   ├── 00_data_exploration.ipynb            # EDA on the labeled URL dataset
│   ├── colab_thumbnail_analysis.ipynb       # Thumbnail fetching + feature extraction (Colab)
│   ├── 03_statistical_analysis.ipynb        # Group comparisons across language groups
│   └── 04_visualization.ipynb              # Publication-ready figures
│
├── scripts/
│   ├── 01_extract_frames.py                 # Optional: full video frame extraction
│   └── 02_analyze_thumbnails.py             # Thumbnail-based visual feature extraction
│
├── results/
│   ├── figures/                             # All 8 figures saved as PNG and PDF
│   │   ├── fig1_luminance_by_language
│   │   ├── fig2_saturation_by_language
│   │   ├── fig3_color_ratios
│   │   ├── fig4_effect_sizes
│   │   ├── fig5_feature_correlations
│   │   ├── fig6_luminance_vs_saturation
│   │   ├── fig7_thumbnail_grid
│   │   └── fig8_text_overlay
│   └── tables/                              # Summary statistics and test results
│       ├── descriptive_stats.csv
│       ├── kruskal_wallis.csv
│       ├── pairwise_mannwhitney.csv
│       ├── effect_sizes.csv
│       └── feature_correlations.csv
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
- Python 3.9+
- A stable internet connection (for thumbnail fetching)

### 1. Clone the repository

```bash
git clone https://github.com/sharyali05/kyrgyz-youtube-visual-audit.git
cd kyrgyz-youtube-visual-audit
```

### 2. Create a Python environment

**Option A — conda (recommended):**
```bash
conda env create -f environment/environment.yml
conda activate kyrgyz-audit
```

**Option B — pip:**
```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r environment/requirements.txt
```

### 3. Install dependencies

```bash
pip install pandas numpy opencv-python requests tqdm Pillow
```

> **Note:** The analysis notebooks are designed to run in **Google Colab** rather than locally, due to DNS resolution issues with WSL2. All Colab notebooks mount Google Drive and read/write data from `kyrgyz-audit/` in your Drive.

---

## Pipeline: Step-by-Step

### Step 1 — Explore the data

Open and run `notebooks/00_data_exploration.ipynb`.

This notebook gives you an overview of the labeled dataset:
- Distribution of language labels
- How many videos are deleted or unreachable?
- Cross-tabulations of language vs. apparent ethnicity labels
- Export of clean URL lists per language group

---

### Step 2 — Extract visual features from thumbnails

Open `notebooks/colab_thumbnail_analysis.ipynb` in Google Colab.

This notebook fetches YouTube thumbnails and computes visual features — no full video download or ffmpeg required. Results are saved directly to Google Drive.

**Color and luminance features:**

| Feature | Description | Method |
|---|---|---|
| `mean_saturation` | Average color saturation | HSV S channel mean |
| `mean_luminance` | Average brightness | HSV V channel mean |
| `saturation_std` | Variability in saturation | Standard deviation |
| `luminance_std` | Variability in brightness | Standard deviation |
| `mean_hue` | Dominant hue | HSV H channel mean |
| `red_ratio` | Proportion of red/orange pixels | HSV hue mask |
| `blue_ratio` | Proportion of blue pixels | HSV hue mask |
| `yellow_ratio` | Proportion of yellow pixels | HSV hue mask |
| `thumbnail_found` | Whether thumbnail was successfully fetched | — |

**Text overlay features** (appended to `visual_features_with_text.csv`):

| Feature | Description | Method |
|---|---|---|
| `text_cell_ratio` | Proportion of grid cells with high edge density | OpenCV edge detection |
| `contrast_score` | Overall image contrast | Otsu thresholding |
| `h_line_score` | Horizontal line density (text line proxy) | Morphological operations |
| `text_overlay_proxy` | Binary flag: likely contains text overlay | Threshold on text_cell_ratio |

> Text overlay detection uses lightweight OpenCV methods rather than EasyOCR to avoid RAM crashes on the free Colab tier.

---

### Step 3 — Statistical analysis

Open and run `notebooks/03_statistical_analysis.ipynb` in Google Colab.

- Descriptive statistics per feature per language group
- Kruskal-Wallis tests across all three language groups
- Mann-Whitney U pairwise tests with Bonferroni correction
- Rank-biserial effect sizes
- Spearman feature correlation matrix

Results saved to `results/tables/`.

---

### Step 4 — Visualization

Open and run `notebooks/04_visualization.ipynb` in Google Colab.

Generates 8 publication-ready figures:

| Figure | Description |
|---|---|
| Fig 1 | Luminance boxplot + violin by language group |
| Fig 2 | Saturation boxplot + violin by language group |
| Fig 3 | Red, blue, yellow pixel ratios by language group |
| Fig 4 | Effect size summary: Russian vs. Kyrgyz |
| Fig 5 | Spearman correlation heatmap between features |
| Fig 6 | Luminance vs. saturation scatter with group centroids |
| Fig 7 | Sample thumbnail grid: brightest vs. least bright |
| Fig 8 | Text overlay density by language group |

---

## Connecting Results to Theory

| Community claim | Operationalization | Finding |
|---|---|---|
| "Kyrgyz cartoons are static / boring" | Mean luminance, saturation | Russian significantly brighter (r = 0.36) |
| "Russian content is more colorful / professional" | Mean saturation, mean luminance | Trend confirmed; luminance significant |
| "Russian content has vlogger aesthetics" | Text overlay density, contrast score | Russian > Kyrgyz (p = 0.064, trending) |
| Kyrgyz = distinct not deficient | Blue pixel ratio | Kyrgyz higher blue — different register |

Findings should be interpreted alongside qualitative interview data. The goal is triangulation: do computational patterns confirm, complicate, or contradict what community members report?

---

## Limitations

- **Thumbnail as proxy**: Thumbnails are designed for maximum visual appeal and may not represent in-video aesthetics accurately.
- **Video availability**: Many videos have been deleted since original data collection, reducing effective sample sizes.
- **Text overlay detection**: The OpenCV-based method detects edge density as a proxy for text and cannot distinguish text from other high-contrast visual elements.
- **Animation vs. live action**: Color and luminance metrics may behave differently for animated vs. live-action content. Future work should analyze these subgroups separately.
- **Language label quality**: Language labels were applied by human annotators. Inter-rater reliability scores should be reported if available.
- **Causal inference**: This study is observational. Visual differences between language groups do not establish that thumbnail aesthetics cause children's language preferences.

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
| Sharazad | Computational analysis, pipeline development |
| Nel | Research design, network analysis conceptualization |

---

## License

Code is released under the MIT License. See `LICENSE` for details. Data is released under CC BY 4.0.
