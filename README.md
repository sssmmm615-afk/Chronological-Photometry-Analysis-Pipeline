# Chronological-Photometry-Analysis-Pipeline
This repository contains a Python script for batch analysis of long-term fiber photometry data. The pipeline performs tdTomato-based regression correction, signal detrending, Z-score normalization, ΔF/F calculation, and peak/AUC quantification, and outputs summary tables and figures for defined time blocks.

## Overview
This repository provides a Python-based batch analysis pipeline for long-term fiber photometry data.
The pipeline is designed for chronological analysis of extended recordings and performs:

- tdTomato-based regression correction
- Signal detrending
- Z-score normalization
- ΔF/F calculation
- Peak detection and AUC quantification

All analyses are performed in predefined time blocks, and the pipeline outputs summary tables and figures suitable for downstream statistical analysis and publication.

---

## Features
- Batch processing of long-duration photometry recordings
- Full-trace Z-score normalization
- Time-segmented analysis (e.g., 2–4 h, 4–6 h)
- Automatic export of:
  - Z-score and ΔF/F traces
  - Peak and AUC metrics
  - Summary tables (CSV, Excel)
  - Figures (SVG)

---

## Requirements
- Python 3.9 or later  
- numpy  
- pandas  
- scipy  
- matplotlib  

(Additional standard scientific Python packages may be required depending on the analysis configuration.)

---

## Usage
1. Place photometry data files (CSV or ppd-converted CSV) in the input directory.
2. Run the main analysis script:

```bash
python run_photometry_analysis.py

