# Long-term Fiber Photometry Batch Analysis Pipeline

## Introduction

This repository provides a Python-based batch analysis pipeline for long-term fiber photometry recordings exported as lock-in demodulated CSV files. The pipeline was developed to support reproducible analysis of recordings spanning several hours, where consistent baseline definition and transparent preprocessing steps are essential for reliable interpretation and group-level comparison.

Each recording is assumed to correspond to a single animal and to contain a time column (in seconds) together with two fluorescence channels: a calcium-dependent signal channel (e.g., 465 nm / GFP) and an isosbestic or reference channel (e.g., 405 nm / Tomato). To accommodate minor variations in CSV export formats, the script automatically detects the appropriate header row and extracts the relevant columns based on common naming conventions.

## Data Processing Workflow

The analysis follows a standard long-term photometry workflow, implemented in a fully automated and batch-oriented manner.

First, a photobleaching correction is applied independently to each fluorescence channel. This correction estimates a linear trend from an early recording window and a late window anchored to the end of the recording, and subtracts this trend from the raw signal. This approach provides a simple and robust correction for slow signal drift over long durations.

Next, motion correction is performed using linear regression, in which the reference channel (405 nm) is fitted to the signal channel (465 nm). The fitted component is then subtracted from the signal channel, reducing motion-related and shared noise components while preserving calcium-dependent dynamics.

Following these corrections, the motion-corrected signal is converted to a Z-score–normalized trace using a fixed global baseline interval.

## Baseline Definition and Normalization

Z-score normalization is performed using a single global baseline interval (default: 25–35 minutes after recording onset). The mean and standard deviation calculated from this interval are applied uniformly across the entire recording and across all animals.

This baseline strategy is intentionally conservative and is particularly well suited for long-term experiments. By avoiding window-specific or adaptive baseline recalculation, the pipeline ensures that differences observed across time or between animals reflect genuine signal dynamics rather than changes in normalization criteria. Photobleaching correction and Z-score normalization are treated as conceptually separate steps.

## Long-term Window Analysis

To summarize sustained neural activity over extended periods, quantitative metrics are calculated within predefined long-term windows (by default, 2–4 hours and 4–6 hours after recording onset). All metrics are computed from the already Z-score–normalized signal, without further baseline adjustment.

For each window, the pipeline reports the mean and standard deviation of the Z-score signal, the area under the curve (AUC), the maximum Z-score (peak amplitude), and the time at which this peak occurs. Together, these metrics provide a compact description of long-duration signal dynamics while preserving the full temporal information in the underlying trace.

## Output Files and Organization

The pipeline produces both per-animal and group-level outputs in formats suitable for archiving and publication.

For each animal, a processed CSV file is generated containing the corrected fluorescence signals and the final Z-score trace. In addition, an SVG figure showing the Z-score trace over the long-term recording period is saved, allowing direct use in figure preparation workflows.

At the group level, two Excel files are generated. The first, `summary_analysis.xlsx`, contains per-animal quantitative metrics along with an additional sheet explaining the meaning of each metric. The second, `all_animals_traces.xlsx`, aggregates all animals’ Z-score traces onto a common time axis and provides a second-binned mean table, facilitating downstream computation of group averages, variability measures, or long-term plots.

## Reproducibility and Intended Use

All analysis parameters, including baseline intervals, photobleaching windows, and plotting ranges, are explicitly defined and configurable via command-line arguments. The pipeline requires no interactive steps or manual adjustment, ensuring that analyses can be rerun under identical conditions.

This repository is intended to serve as a transparent record of the analysis pipeline used for long-term fiber photometry data and to support reproducible sharing alongside manuscripts, supplementary materials, or collaborative projects involving extended-duration neural recordings.
