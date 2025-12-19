Long-term Fiber Photometry Batch Analysis

This repository provides a Python batch analysis pipeline for long-term fiber photometry recordings, designed for lock-in demodulated CSV files.
The script processes per-animal photometry data and generates standardized Z-score traces, quantitative metrics, and summary outputs suitable for long-duration experiments.

Overview

This pipeline performs the following steps for each animal:

Photobleaching correction
Linear correction using early and late recording windows.

Motion correction
Linear regression–based correction of the calcium-dependent channel using the isosbestic control channel (405 → 465).

Z-score normalization
Normalization using a fixed global baseline interval, ensuring consistency across long recordings and animals.

Long-term window analysis
Quantification of mean, standard deviation, AUC, peak amplitude, and peak timing in predefined time windows (e.g., 2–4 h, 4–6 h).

Batch summary and aggregation
Export of per-animal results and second-binned group-average Z-score traces.

Input Data

Lock-in demodulated CSV files

One file per animal

Each CSV must contain:

A time column (seconds)

A calcium-dependent fluorescence channel (e.g., GFP / 465 nm)

An isosbestic or control channel (e.g., Tomato / 405 nm)

The script automatically detects the header row within the first few lines and is robust to minor format differences.

Output Files
Per-animal outputs

Processed CSV file containing:

Photobleaching-corrected signals

Motion-corrected signals

Z-score–normalized trace

SVG figure of the Z-score trace over the long-term recording period

Summary outputs

summary_analysis.xlsx

Summary sheet: per-animal quantitative metrics

Explanation sheet: definition of each metric

all_animals_traces.xlsx

Second-binned mean Z-score trace across animals

Baseline Strategy
Z-score normalization

Z-score normalization is performed using a fixed global baseline interval (default: 25–35 min after recording onset).

The same baseline definition is applied to all animals and all time windows.

This approach is particularly suitable for long-duration recordings, as it avoids window-specific or post hoc baseline redefinition.

Photobleaching correction

Photobleaching is corrected independently of Z-score normalization.

A linear trend is estimated using:

An early recording window

A late recording window anchored to the end of the recording

The fitted trend is subtracted from the raw fluorescence signal.

Analysis Windows

Quantitative metrics are calculated on Z-score–normalized signals for predefined long-term windows, such as:

2–4 hours

4–6 hours

No additional baseline recalculation is performed for these windows.

Typical Use Cases

Long-term fiber photometry experiments (several hours)

Hormonal or metabolic signaling with delayed neural responses

Group-level comparison of sustained neural activity dynamics

Reproducible batch analysis for publication-quality data

Reproducibility

All parameters (baseline intervals, photobleaching windows, plotting ranges) are explicitly defined and configurable via command-line arguments.

No interactive steps or manual adjustments are required.

The script reflects the exact analysis pipeline used for data processing, ensuring full reproducibility.

License

This project is intended for open scientific use.
A permissive license (e.g., MIT) can be added depending on downstream requirements.
