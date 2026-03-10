"""
Slug detection via background subtraction.

Produces:
  1. frames/median_bg.png        - median background image
  2. frames/std_heatmap.png      - temporal variation heatmap
  3. frames/overlay_std.mp4      - original video with std heatmap overlay
  4. frames/overlay_diff.mp4     - original video with per-frame diff overlay
  5. frames/intensity_plot.png   - mean intensity over time in high-variation region
"""

import cv2
import numpy as np
import sys

VIDEO = "pioreactor_focus_10s_v2.mp4"
OUT = "."
ALPHA = 0.4  # overlay transparency


def load_frames(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames_bgr = []
    frames_gray = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames_bgr.append(frame)
        frames_gray.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32))
    cap.release()
    h, w = frames_gray[0].shape
    return frames_bgr, frames_gray, fps, h, w


def main():
    import os
    os.makedirs(OUT, exist_ok=True)

    print("Loading video...")
    frames_bgr, frames_gray, fps, h, w = load_frames(VIDEO)
    print(f"  {len(frames_gray)} frames, {w}x{h} @ {fps:.0f} fps")

    stack = np.array(frames_gray)

    # 1. Median background
    print("Computing median background...")
    median_bg = np.median(stack, axis=0)
    cv2.imwrite(f"{OUT}/median_bg.png", median_bg.astype(np.uint8))

    # 2. Temporal std heatmap (where things change most across the video)
    print("Computing temporal std map...")
    std_map = np.std(stack, axis=0)
    std_norm = (std_map / (std_map.max() + 1e-6) * 255).astype(np.uint8)
    std_color = cv2.applyColorMap(std_norm, cv2.COLORMAP_JET)
    cv2.imwrite(f"{OUT}/std_heatmap.png", std_color)

    # 3. Overlay video: std heatmap burned onto every frame
    print("Writing std overlay video...")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_std = cv2.VideoWriter(f"{OUT}/overlay_std.mp4", fourcc, fps, (w, h))
    for bgr in frames_bgr:
        blended = cv2.addWeighted(bgr, 1.0 - ALPHA, std_color, ALPHA, 0)
        # Add label
        cv2.putText(blended, "Temporal Std Heatmap", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        out_std.write(blended)
    out_std.release()

    # 4. Per-frame diff overlay video
    print("Writing per-frame diff overlay video...")
    out_diff = cv2.VideoWriter(f"{OUT}/overlay_diff.mp4", fourcc, fps, (w, h))
    max_diff_global = 0
    diffs = []
    for gray in frames_gray:
        d = np.abs(gray - median_bg)
        diffs.append(d)
        max_diff_global = max(max_diff_global, d.max())

    for i, (bgr, d) in enumerate(zip(frames_bgr, diffs)):
        # Normalize diff to 0-255 using global max for consistency
        d_norm = (d / (max_diff_global + 1e-6) * 255).astype(np.uint8)
        d_color = cv2.applyColorMap(d_norm, cv2.COLORMAP_JET)
        blended = cv2.addWeighted(bgr, 1.0 - ALPHA, d_color, ALPHA, 0)
        # Show frame number and mean diff
        mean_d = np.mean(d)
        cv2.putText(blended, f"Frame {i:3d}  diff={mean_d:.1f}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        out_diff.write(blended)
    out_diff.release()

    # 5. Intensity plot over time
    print("Generating intensity plot...")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Whole frame mean
        whole_means = [np.mean(g) for g in frames_gray]

        # High-variation region mean (where std is above 50th percentile of std_map)
        hot_mask = std_map > np.percentile(std_map, 95)
        hot_means = [np.mean(g[hot_mask]) for g in frames_gray]

        times = np.arange(len(frames_gray)) / fps

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
        ax1.plot(times, whole_means, "b-", linewidth=0.8)
        ax1.set_ylabel("Mean Intensity")
        ax1.set_title("Whole Frame")
        ax1.grid(True, alpha=0.3)

        ax2.plot(times, hot_means, "r-", linewidth=0.8)
        ax2.set_ylabel("Mean Intensity")
        ax2.set_xlabel("Time (s)")
        ax2.set_title("High-Variation Region (top 5% std)")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{OUT}/intensity_plot.png", dpi=150)
        plt.close()
    except ImportError:
        print("  matplotlib not available, skipping plot")

    print(f"\nDone! Outputs in {OUT}/")
    print(f"  median_bg.png       - background model")
    print(f"  std_heatmap.png     - where things change most")
    print(f"  overlay_std.mp4     - video with std heatmap overlay")
    print(f"  overlay_diff.mp4    - video with per-frame diff overlay")
    print(f"  intensity_plot.png  - intensity traces over time")


if __name__ == "__main__":
    main()
