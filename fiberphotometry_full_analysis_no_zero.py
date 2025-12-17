import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.signal import find_peaks
from scipy.integrate import simpson
from openpyxl import Workbook

# === 設定 ===
sampling_rate = 2  # Hz
block_duration_sec = 2 * 60 * 60
baseline_duration_sec = 30 * 60
block_points = block_duration_sec * sampling_rate
baseline_points = baseline_duration_sec * sampling_rate
window_size = 301  # 移動中央値のウィンドウサイズ

# === フォルダ設定 ===
desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
input_folder = os.path.join(desktop_path, 'Dric_CSV')
output_folder = os.path.join(desktop_path, 'CSV_finish')
os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# === CSVファイル取得 ===
csv_files = glob.glob(os.path.join(input_folder, '*.csv'))
sample_names = [os.path.splitext(os.path.basename(f))[0] for f in csv_files]

if not csv_files:
    print("⚠ Dric_CSV フォルダにCSVファイルがありません。")
else:
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        base_name = os.path.splitext(filename)[0]
        print(f"▶ 処理中: {filename}")

        try:
            df = pd.read_csv(file_path, header=1)
            gfp_col = [col for col in df.columns if 'gfp' in col.lower()]
            tdt_col = [col for col in df.columns if 'tdtomato' in col.lower() or 'red' in col.lower() or 'tomato' in col.lower()]
            if not gfp_col or not tdt_col:
                print(f"⚠ カラムが見つかりません（{filename}）")
                continue

            gfp_all = df[gfp_col[0]].astype(float).values
            tdt_all = df[tdt_col[0]].astype(float).values
            total_points = min(len(gfp_all), len(tdt_all))
            num_blocks = min(3, total_points // block_points)

            for i in range(num_blocks):
                start = i * block_points
                end = start + block_points

                gfp = gfp_all[start:end].reshape(-1, 1)
                tdt = tdt_all[start:end].reshape(-1, 1)
                if len(gfp) < block_points:
                    continue

                block_label = f"{i*2}to{(i+1)*2}h"
                sample_folder = os.path.join(output_folder, base_name)
                block_output_folder = os.path.join(sample_folder, block_label)
                result_folder = os.path.join(block_output_folder, 'result')
                summary_folder = os.path.join(block_output_folder, 'summary')
                os.makedirs(result_folder, exist_ok=True)
                os.makedirs(summary_folder, exist_ok=True)

                gfp_smooth = pd.Series(gfp.flatten()).rolling(window=window_size, center=True, min_periods=1).median().values
                gfp_detrended = gfp.flatten() - gfp_smooth

                model = LinearRegression()
                model.fit(tdt, gfp_detrended.reshape(-1, 1))
                gfp_fitted = model.predict(tdt)
                gfp_corrected = gfp_detrended.reshape(-1, 1) - gfp_fitted

                baseline = gfp_corrected[:baseline_points]
                z_score = (gfp_corrected - np.mean(baseline)) / np.std(baseline)
                z_score = z_score.flatten()
                time_axis_min = np.arange(len(z_score)) / (sampling_rate * 60)
                valid_idx = time_axis_min != 0  # 0分を除く

                baseline_fluo = np.mean(gfp[:baseline_points])
                delta_f_over_f = (gfp.flatten() - baseline_fluo) / baseline_fluo
                delta_f_over_f_z = (delta_f_over_f - np.mean(delta_f_over_f[:baseline_points])) / np.std(delta_f_over_f[:baseline_points])

                peaks, _ = find_peaks(z_score, height=2)
                auc = simpson(z_score[z_score > 0])
                z_peaks = z_score[peaks]
                z_peak_mean = np.mean(z_peaks) if len(z_peaks) > 0 else np.nan
                z_peak_std = np.std(z_peaks) if len(z_peaks) > 0 else np.nan

                # 2〜6h ΔF/F
                start_idx = int(2 * 60 * sampling_rate)
                end_idx = int(6 * 60 * sampling_rate)
                if end_idx <= len(time_axis_min):
                    deltaf_window = delta_f_over_f_z[start_idx:end_idx]
                    deltaf_auc = simpson(deltaf_window)
                    deltaf_peak = np.max(deltaf_window)
                    deltaf_mean = np.mean(deltaf_window)
                    deltaf_sd = np.std(deltaf_window)
                else:
                    deltaf_auc = np.nan
                    deltaf_peak = np.nan
                    deltaf_mean = np.nan
                    deltaf_sd = np.nan

                summary_df = pd.DataFrame({
                    'AUC': [auc],
                    'Peak_Count': [len(peaks)],
                    'Z_score_Peaks_Mean': [z_peak_mean],
                    'Z_score_Peaks_SD': [z_peak_std],
                    'DeltaF_2to6h_AUC': [deltaf_auc],
                    'DeltaF_2to6h_Peak': [deltaf_peak],
                    'DeltaF_2to6h_Mean': [deltaf_mean],
                    'DeltaF_2to6h_SD': [deltaf_sd]
                })

                with pd.ExcelWriter(os.path.join(summary_folder, "summary.xlsx"), engine='openpyxl') as writer:
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # グラフ出力
                plt.figure()
                plt.plot(time_axis_min[valid_idx], gfp[valid_idx], label='GFP (raw)', color='green')
                plt.plot(time_axis_min[valid_idx], tdt[valid_idx], label='tdTomato', color='red')
                plt.legend()
                plt.title(f"{base_name}_{block_label} - Signal vs Control")
                plt.xlabel('Time (min)')
                plt.ylabel('Fluorescence')
                plt.savefig(os.path.join(block_output_folder, "signal_vs_control.svg"))
                plt.close()

                plt.figure()
                plt.plot(time_axis_min[valid_idx], gfp_detrended[valid_idx], label='GFP Detrended', color='green')
                plt.plot(time_axis_min[valid_idx], gfp_fitted[valid_idx], label='Fitted GFP from tdTomato', color='red')
                plt.legend()
                plt.title(f"{base_name}_{block_label} - Fitted Control")
                plt.xlabel('Time (min)')
                plt.ylabel('Signal')
                plt.savefig(os.path.join(block_output_folder, "fitted_control.svg"))
                plt.close()

                plt.figure()
                plt.plot(time_axis_min[valid_idx], delta_f_over_f[valid_idx], label='Delta F/F', color='green')
                plt.plot(time_axis_min[valid_idx], delta_f_over_f_z[valid_idx], label='Normalized Delta F/F', color='red')
                plt.legend()
                plt.title(f"{base_name}_{block_label} - Delta F/F")
                plt.xlabel('Time (min)')
                plt.ylabel('Value')
                plt.savefig(os.path.join(block_output_folder, "deltaF.svg"))
                plt.close()

                if end_idx <= len(time_axis_min):
                    plt.figure()
                    plt.plot(time_axis_min[start_idx:end_idx], delta_f_over_f[start_idx:end_idx], label='Delta F/F', color='green')
                    plt.plot(time_axis_min[start_idx:end_idx], delta_f_over_f_z[start_idx:end_idx], label='Normalized Delta F/F', color='red')
                    plt.legend()
                    plt.title(f"{base_name}_{block_label} - Delta F/F (2h-6h)")
                    plt.xlabel('Time (min)')
                    plt.ylabel('Value')
                    plt.savefig(os.path.join(block_output_folder, "deltaF_2to6h.svg"))
                    plt.close()

                plt.figure()
                plt.plot(time_axis_min[valid_idx], z_score[valid_idx], label='Z-score')
                valid_peaks = peaks[time_axis_min[peaks] != 0]
                plt.plot(time_axis_min[valid_peaks], z_score[valid_peaks], "x", label='Peaks')
                plt.legend()
                plt.title(f"{base_name}_{block_label} - Z-score Peaks")
                plt.xlabel('Time (min)')
                plt.ylabel('Z')
                plt.savefig(os.path.join(block_output_folder, "zscore_peaks.svg"))
                plt.close()

                print(f"✅ {base_name}_{block_label} 完了")

        except Exception as e:
            print(f"❌ エラー（{filename}）: {e}")

# summary統合
all_summaries = []
for sample_name in sample_names:
    sample_folder = os.path.join(output_folder, sample_name)
    if not os.path.isdir(sample_folder):
        continue
    for block_folder in os.listdir(sample_folder):
        summary_path = os.path.join(sample_folder, block_folder, 'summary', 'summary.xlsx')
        if os.path.exists(summary_path):
            df = pd.read_excel(summary_path, engine='openpyxl')
            df.insert(0, 'Sample', sample_name)
            df.insert(1, 'Block', block_folder)
            all_summaries.append(df)

if all_summaries:
    all_summary_df = pd.concat(all_summaries, ignore_index=True)
    all_summary_path = os.path.join(output_folder, 'All_summary.xlsx')
    all_summary_df.to_excel(all_summary_path, index=False)
    print(f"📊 All_summary.xlsx 出力完了: {all_summary_path}")
else:
    print("⚠ 統合対象 summary.xlsx が見つかりませんでした。")
