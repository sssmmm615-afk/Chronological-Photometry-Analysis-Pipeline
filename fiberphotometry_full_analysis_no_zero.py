#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Long-term fiber photometry batch analysis script (GitHub-ready)
(For lock-in demodulated CSV files)

This version is intended to reproduce the same results as the "paper-used" code:
- Uses pandas Series mean/std behavior (std uses ddof=1 by default)
- No extra fail-safe branches that could change outputs
- No personal paths; all paths are CLI-configurable

Inputs:
- CSV files in a specified data directory (one file per animal)

Outputs:
(1) Per-animal processed CSV (Z-score trace etc.) + SVG trace plot
(2) summary_analysis.xlsx (with an explanation sheet)
(3) all_animals_traces.xlsx (second-binned mean across animals)

Assumptions:
- Each CSV contains columns for Time and fluorescence channels (e.g., GFP/465 and Tomato/405)
- The header row may appear within the first 5 lines
- Animal ID is inferred from the file name as the prefix before the first underscore ("_")
"""

import os
import glob
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# Processing functions (paper-matched behavior)
# -----------------------------
def correct_photobleaching(ts, ys, pre_interval, post_interval):
    """
    Simple linear photobleaching correction using means from two time windows.
    Returns ys with a fitted line (from pre/post means) subtracted.

    NOTE: Kept consistent with the original/paper-used script (no extra fail-safes).
    """
    pre_mask = (ts >= pre_interval[0]) & (ts <= pre_interval[1])
    post_mask = (ts >= post_interval[0]) & (ts <= post_interval[1])

    pre_mean = ys[pre_mask].mean()
    post_mean = ys[post_mask].mean()

    slope = (post_mean - pre_mean) / (post_interval[1] - pre_interval[0])
    intercept = pre_mean - slope * pre_interval[0]
    return ys - (slope * ts + intercept)


def correct_motion(fluo465, fluo405):
    """
    Motion correction by linear regression of 405 onto 465:
    465_corrected = 465 - (fit(405)->465 - mean(fit))

    NOTE: Kept consistent with the original/paper-used script.
    """
    A = np.vstack([fluo405, np.ones_like(fluo405)]).T
    coeffs, _, _, _ = np.linalg.lstsq(A, fluo465, rcond=None)
    fitted = A @ coeffs
    return fluo405, fluo465 - (fitted - np.mean(fitted))


def transform_to_zscore(ts, ys, baseline_interval=(0, 60)):
    """
    Z-score normalization using a global baseline interval.

    CRITICAL:
    - Uses pandas Series .std() default (ddof=1), matching the paper-used code.
    """
    mask = (ts >= baseline_interval[0]) & (ts <= baseline_interval[1])
    baseline_mean = ys[mask].mean()
    baseline_std = ys[mask].std()  # pandas default ddof=1
    return (ys - baseline_mean) / baseline_std


def compute_auc(ts, ys):
    return np.trapz(ys, ts)


def compute_peak(ys):
    idx = int(np.argmax(ys))
    return float(ys[idx]), idx


def read_and_clean_csv(filepath):
    """
    Detect the true header row within the first 5 lines (looking for 'Time' and 'gfp'),
    then read that CSV into a DataFrame and keep Time/GFP/Tomato-related columns.

    NOTE:
    - Mirrors the paper-used behavior: open() without explicit encoding.
    """
    with open(filepath, "r") as f:
        lines = f.readlines()

    header_candidates = [line.strip().split(",") for line in lines[:5]]
    true_header_line = None
    for i, cols in enumerate(header_candidates):
        if any("Time" in c for c in cols) and any("gfp" in c.lower() for c in cols):
            true_header_line = i
            break

    if true_header_line is None:
        raise ValueError(f"Header row not found within first 5 lines: {filepath}")

    df = pd.read_csv(filepath, skiprows=true_header_line)
    df.columns = [c.strip() for c in df.columns]

    required_cols = [
        c for c in df.columns
        if ("Time" in c) or ("gfp" in c.lower()) or ("tomato" in c.lower())
    ]
    if len(required_cols) == 0:
        raise ValueError(f"Required columns not found (Time/GFP/Tomato): {filepath}")

    return df[required_cols]


# -----------------------------
# Main
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Long-term fiber photometry batch analysis (lock-in demodulated CSV -> Z-score, metrics, SVG, Excel)."
    )

    # Paths (generic)
    parser.add_argument("--data_dir", type=str, default="./Dric_CSV",
                        help="Input directory containing raw CSV files.")
    parser.add_argument("--out_data_dir", type=str, default="./Dric_CSV_Finish",
                        help="Output directory for per-animal CSV/SVG.")
    parser.add_argument("--summary_out_dir", type=str, default="./Dric_CSV_Summary",
                        help="Output directory for summary Excel files.")

    # Baseline / windows
    parser.add_argument("--baseline_global_start", type=float, default=1500.0,
                        help="Global baseline interval start (s) for Z-score.")
    parser.add_argument("--baseline_global_end", type=float, default=2100.0,
                        help="Global baseline interval end (s) for Z-score.")

    parser.add_argument("--pb_pre_start", type=float, default=100.0,
                        help="Photobleaching pre-window start (s).")
    parser.add_argument("--pb_pre_end", type=float, default=600.0,
                        help="Photobleaching pre-window end (s).")

    # End-anchored post window: [max_time - pb_post_start, max_time - pb_post_end]
    parser.add_argument("--pb_post_start", type=float, default=500.0,
                        help="Photobleaching post-window offset start from end (s).")
    parser.add_argument("--pb_post_end", type=float, default=0.0,
                        help="Photobleaching post-window offset end from end (s).")

    # Plot window
    parser.add_argument("--plot_start", type=float, default=2700.0,
                        help="Plot start time (s).")
    parser.add_argument("--plot_end_cap", type=float, default=24300.0,
                        help="Plot end time cap (s).")

    args = parser.parse_args()

    data_dir = args.data_dir
    out_data_dir = args.out_data_dir
    summary_out_dir = args.summary_out_dir

    os.makedirs(out_data_dir, exist_ok=True)
    os.makedirs(summary_out_dir, exist_ok=True)

    baseline_interval_global = (args.baseline_global_start, args.baseline_global_end)

    window_defs = {
        "2-4h": (7200.0, 14400.0),
        "4-6h": (14400.0, 21600.0),
    }

    all_means = {}

    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Input directory not found: {data_dir}")

    phmtry_files = [f for f in os.listdir(data_dir) if f.lower().endswith(".csv")]
    if len(phmtry_files) == 0:
        print(f"No CSV files found in: {data_dir}")
        return

    # -----------------------------
    # Per-animal processing
    # -----------------------------
    for phmtry_file in phmtry_files:
        print(f"\n=== Processing: {phmtry_file} ===")
        animal = phmtry_file.split("_")[0]
        filepath = os.path.join(data_dir, phmtry_file)

        try:
            df_raw = read_and_clean_csv(filepath)
        except Exception as e:
            print(f"Skipping (read error): {e}")
            continue

        # Map columns into standardized names
        col_map = {}
        for col in df_raw.columns:
            if "Time" in col:
                col_map[col] = "time"
            elif "gfp" in col.lower():
                col_map[col] = "F-465"
            elif "tomato" in col.lower():
                col_map[col] = "AF-405"

        # Ensure required standardized columns exist
        df = df_raw.rename(columns=col_map)
        required = ["time", "F-465", "AF-405"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            print(f"Skipping (missing columns {missing}): {phmtry_file}")
            continue

        df = df[required].dropna()

        # Photobleaching correction intervals
        max_time = float(df["time"].max())
        pre_interval = (args.pb_pre_start, args.pb_pre_end)
        post_interval = (max_time - args.pb_post_start, max_time - args.pb_post_end)

        df["fluo465-pbc"] = correct_photobleaching(df["time"], df["F-465"], pre_interval, post_interval)
        df["fluo405-pbc"] = correct_photobleaching(df["time"], df["AF-405"], pre_interval, post_interval)

        df["fluo405-maf"], df["fluo465-mac"] = correct_motion(df["fluo465-pbc"].values, df["fluo405-pbc"].values)
        # Put back into Series aligned with df index
        df["fluo405-maf"] = pd.Series(df["fluo405-maf"], index=df.index)
        df["fluo465-mac"] = pd.Series(df["fluo465-mac"], index=df.index)

        df["fluo465-zsc"] = transform_to_zscore(df["time"], df["fluo465-mac"], baseline_interval=baseline_interval_global)

        # Save per-animal processed CSV
        csv_out_path = os.path.join(out_data_dir, f"{animal}-phmtry.csv")
        df.to_csv(csv_out_path, index=False)

        # SVG plot (plot_start to min(plot_end_cap, max_time))
        plot_end_time = min(args.plot_end_cap, max_time)
        df_window = df[(df["time"] >= args.plot_start) & (df["time"] <= plot_end_time)]

        plt.figure(figsize=(12, 4))
        plt.plot(df_window["time"], df_window["fluo465-zsc"], color="tab:blue")
        plt.xlabel("Time (s)")
        plt.ylabel("Z-score")
        plt.title(f"{animal} - Z-Score ({args.plot_start/60:.0f}min - {plot_end_time/3600:.2f}h)")
        plt.tight_layout()

        svg_path = os.path.join(out_data_dir, f"{animal}-trace.svg")
        plt.savefig(svg_path, format="svg")
        plt.close()
        print(f"Saved SVG: {svg_path}")

        # Metrics per window
        animal_metrics = {}
        for label, (start_t, end_t) in window_defs.items():
            win_start = max(args.plot_start, start_t)
            win_end = min(end_t, plot_end_time)
            if win_start >= win_end:
                continue

            w = df[(df["time"] >= win_start) & (df["time"] < win_end)].reset_index(drop=True)
            if len(w) == 0:
                continue

            mean_z = float(w["fluo465-zsc"].mean())
            std_z = float(w["fluo465-zsc"].std())  # pandas ddof=1
            auc_z = float(compute_auc(w["time"].values, w["fluo465-zsc"].values))
            peak_z, peak_idx = compute_peak(w["fluo465-zsc"].values)
            peak_time = float(w.loc[peak_idx, "time"])

            animal_metrics[f"{label}_mean"] = mean_z
            animal_metrics[f"{label}_std"] = std_z
            animal_metrics[f"{label}_auc"] = auc_z
            animal_metrics[f"{label}_peak"] = peak_z
            animal_metrics[f"{label}_peak_time"] = peak_time

            print(
                f"{label}: mean={mean_z:.3f}, std={std_z:.3f}, auc={auc_z:.3f}, "
                f"peak={peak_z:.3f}, peak_time={peak_time:.1f}"
            )

        all_means[animal] = animal_metrics

    # -----------------------------
    # Summary Excel (with explanation sheet)
    # -----------------------------
    results_list = []
    for animal, metrics in all_means.items():
        row = {"animal": animal}
        row.update(metrics)
        results_list.append(row)
    results_df = pd.DataFrame(results_list)

    explanation_data = [
        {"Item": "mean", "Description": "Mean Z-score within the interval"},
        {"Item": "std", "Description": "Standard deviation within the interval"},
        {"Item": "auc", "Description": "Area Under the Curve (integral of Z-score within the interval)"},
        {"Item": "peak", "Description": "Maximum Z-score within the interval"},
        {"Item": "peak_time", "Description": "Time (s) at which the peak occurs"},
    ]
    explanation_df = pd.DataFrame(explanation_data)

    excel_out_path = os.path.join(summary_out_dir, "summary_analysis.xlsx")
    with pd.ExcelWriter(excel_out_path) as writer:
        results_df.to_excel(writer, sheet_name="Summary", index=False)
        explanation_df.to_excel(writer, sheet_name="Explanation", index=False)
    print(f"\n✅ Saved summary Excel (2 sheets): {excel_out_path}")

    # -----------------------------
    # All-animal trace aggregation Excel (second-binned mean)
    # -----------------------------
    trace_files = glob.glob(os.path.join(out_data_dir, "*-phmtry.csv"))
    all_traces = None
    all_plot_end_times = []

    for fpath in trace_files:
        df_trace = pd.read_csv(fpath)
        animal_name = os.path.basename(fpath).split("-")[0]

        if "time" not in df_trace.columns or "fluo465-zsc" not in df_trace.columns:
            continue

        max_time_animal = float(df_trace["time"].max())
        plot_end_time_animal = min(args.plot_end_cap, max_time_animal)
        all_plot_end_times.append(plot_end_time_animal)

        df_trace = df_trace[["time", "fluo465-zsc"]].rename(columns={"fluo465-zsc": animal_name})

        if all_traces is None:
            all_traces = df_trace
        else:
            all_traces = pd.merge(all_traces, df_trace, on="time", how="outer")

    if all_traces is None or len(all_plot_end_times) == 0:
        print("No per-animal trace files found for aggregation.")
        return

    global_plot_end_time = min(all_plot_end_times)
    all_traces = all_traces[(all_traces["time"] >= args.plot_start) & (all_traces["time"] <= global_plot_end_time)]

    # Second-binning: round to int seconds, then average where multiple samples fall in the same second
    all_traces["time"] = all_traces["time"].round().astype(int)
    all_traces_reduced = all_traces.groupby("time").mean().reset_index().sort_values("time")

    all_zscore_out = os.path.join(summary_out_dir, "all_animals_traces.xlsx")
    all_traces_reduced.to_excel(all_zscore_out, index=False)
    print(f"✅ Saved all-animal trace Excel: {all_zscore_out}")


if __name__ == "__main__":
    main()
