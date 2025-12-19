Long-term Fiber Photometry Batch Analysis
This repository provides a Python batch analysis pipeline for long-term fiber photometry recordings, designed for lock-in demodulated CSV files.
The script processes per-animal photometry data and generates standardized Z-score traces, quantitative metrics, and summary outputs suitable for long-duration experiments.
________________________________________
Overview
This pipeline performs the following steps for each animal:
1.	Photobleaching correction
Linear correction using early and late recording windows.
2.	Motion correction
Linear regression–based correction of the calcium-dependent channel using the isosbestic control channel (405 → 465).
3.	Z-score normalization
Normalization using a fixed global baseline interval, ensuring consistency across long recordings and animals.
4.	Long-term window analysis
Quantification of mean, standard deviation, AUC, peak amplitude, and peak timing in predefined time windows (e.g., 2–4 h, 4–6 h).
5.	Batch summary and aggregation
Export of per-animal results and second-binned group-average Z-score traces.
________________________________________
Input Data
•	Lock-in demodulated CSV files
•	One file per animal
•	Each CSV must contain:
o	A time column (seconds)
o	A calcium-dependent fluorescence channel (e.g., GFP / 465 nm)
o	An isosbestic or control channel (e.g., Tomato / 405 nm)
The script automatically detects the header row within the first few lines and is robust to minor format differences.
________________________________________
Output Files
Per-animal outputs
•	Processed CSV file containing:
o	Photobleaching-corrected signals
o	Motion-corrected signals
o	Z-score–normalized trace
•	SVG figure of the Z-score trace over the long-term recording period
Summary outputs
•	summary_analysis.xlsx
o	Summary sheet: per-animal quantitative metrics
o	Explanation sheet: definition of each metric
•	all_animals_traces.xlsx
o	Second-binned mean Z-score trace across animals
________________________________________
Baseline Strategy
Z-score normalization
•	Z-score normalization is performed using a fixed global baseline interval (default: 25–35 min after recording onset).
•	The same baseline definition is applied to all animals and all time windows.
•	This approach is particularly suitable for long-duration recordings, as it avoids window-specific or post hoc baseline redefinition.
Photobleaching correction
•	Photobleaching is corrected independently of Z-score normalization.
•	A linear trend is estimated using:
o	An early recording window
o	A late recording window anchored to the end of the recording
•	The fitted trend is subtracted from the raw fluorescence signal.
________________________________________
Analysis Windows
Quantitative metrics are calculated on Z-score–normalized signals for predefined long-term windows, such as:
•	2–4 hours
•	4–6 hours
No additional baseline recalculation is performed for these windows.
________________________________________
Typical Use Cases
•	Long-term fiber photometry experiments (several hours)
•	Hormonal or metabolic signaling with delayed neural responses
•	Group-level comparison of sustained neural activity dynamics
•	Reproducible batch analysis for publication-quality data
________________________________________
Reproducibility
•	All parameters (baseline intervals, photobleaching windows, plotting ranges) are explicitly defined and configurable via command-line arguments.
•	No interactive steps or manual adjustments are required.
•	The script reflects the exact analysis pipeline used for data processing, ensuring full reproducibility.
________________________________________
License
This project is intended for open scientific use.
A permissive license (e.g., MIT) can be added depending on downstream requirements.

