"""
2x2 comparison figure of slug detection methods for poster.
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

VIDEO = "pioreactor_focus_10s_v2.mp4"
FRAME_IDX = 60  # mid-transit frame
DIFF_THRESH = 5.0


def load_video():
    cap = cv2.VideoCapture(VIDEO)
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
    return frames_bgr, frames_gray, fps


def make_kalman():
    kf = cv2.KalmanFilter(4, 2)
    dt = 1.0
    kf.transitionMatrix = np.array([
        [1, 0, dt, 0], [0, 1, 0, dt],
        [0, 0, 1, 0], [0, 0, 0, 1],
    ], dtype=np.float32)
    kf.measurementMatrix = np.array([
        [1, 0, 0, 0], [0, 1, 0, 0],
    ], dtype=np.float32)
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 1.0
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 10.0
    kf.errorCovPost = np.eye(4, dtype=np.float32) * 100.0
    return kf


def main():
    print("Loading video...")
    frames_bgr, frames_gray, fps = load_video()
    n = len(frames_gray)
    h, w = frames_gray[0].shape

    stack = np.array(frames_gray)
    median_bg = np.median(stack, axis=0)
    std_map = np.std(stack, axis=0)

    # Search mask
    search_mask = (std_map > np.percentile(std_map, 98)).astype(np.uint8)
    kernel_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51))
    search_mask = cv2.dilate(search_mask, kernel_dilate)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

    frame_bgr = frames_bgr[FRAME_IDX].copy()
    frame_gray = frames_gray[FRAME_IDX]
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    panels = []

    # --- Panel A: Temporal Std Heatmap Overlay ---
    std_norm = (std_map / (std_map.max() + 1e-6) * 255).astype(np.uint8)
    std_color = cv2.applyColorMap(std_norm, cv2.COLORMAP_JET)
    blended_a = cv2.addWeighted(frame_bgr, 0.6, std_color, 0.4, 0)
    panels.append(cv2.cvtColor(blended_a, cv2.COLOR_BGR2RGB))

    # --- Panel B: Median Diff + Circle ---
    panel_b = frame_bgr.copy()
    diff_med = np.abs(frame_gray - median_bg) * search_mask
    mask_med = (diff_med > DIFF_THRESH).astype(np.uint8) * 255
    mask_med = cv2.morphologyEx(mask_med, cv2.MORPH_CLOSE, kernel)
    mask_med = cv2.morphologyEx(mask_med, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(mask_med, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 200:
            (cx, cy), radius = cv2.minEnclosingCircle(largest)
            cv2.circle(panel_b, (int(cx), int(cy)), int(radius) + 20, (0, 255, 0), 3)
    panels.append(cv2.cvtColor(panel_b, cv2.COLOR_BGR2RGB))

    # --- Panel C: Start/End Diff Contours ---
    panel_c = frame_bgr.copy()
    first, last = frames_gray[0], frames_gray[-1]
    for ref, color in [(first, (0, 255, 0)), (last, (255, 255, 0))]:
        diff_ref = np.abs(frame_gray - ref) * search_mask
        mask_ref = (diff_ref > DIFF_THRESH).astype(np.uint8) * 255
        mask_ref = cv2.morphologyEx(mask_ref, cv2.MORPH_CLOSE, kernel)
        mask_ref = cv2.morphologyEx(mask_ref, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(mask_ref, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 200:
                epsilon = 0.01 * cv2.arcLength(largest, True)
                smoothed = cv2.approxPolyDP(largest, epsilon, True)
                cv2.drawContours(panel_c, [smoothed], -1, color, 3)
    panels.append(cv2.cvtColor(panel_c, cv2.COLOR_BGR2RGB))

    # --- Panel D: Median Diff Contour + Kalman ---
    # Run Kalman up to FRAME_IDX to get filtered state
    kf = make_kalman()
    kalman_initialized = False
    for j in range(FRAME_IDX + 1):
        diff_j = np.abs(frames_gray[j] - median_bg) * search_mask
        mask_j = (diff_j > DIFF_THRESH).astype(np.uint8) * 255
        mask_j = cv2.morphologyEx(mask_j, cv2.MORPH_CLOSE, kernel)
        mask_j = cv2.morphologyEx(mask_j, cv2.MORPH_OPEN, kernel)
        contours_j, _ = cv2.findContours(mask_j, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mcx, mcy = None, None
        if contours_j:
            lg = max(contours_j, key=cv2.contourArea)
            if cv2.contourArea(lg) > 200:
                M = cv2.moments(lg)
                if M["m00"] > 0:
                    mcx = M["m10"] / M["m00"]
                    mcy = M["m01"] / M["m00"]
        if mcx is not None:
            meas = np.array([[np.float32(mcx)], [np.float32(mcy)]])
            if not kalman_initialized:
                kf.statePost = np.array([
                    [np.float32(mcx)], [np.float32(mcy)],
                    [np.float32(0)], [np.float32(0)],
                ])
                kalman_initialized = True
            kf.predict()
            kf.correct(meas)
        elif kalman_initialized:
            kf.predict()

    panel_d = frame_bgr.copy()
    # Draw contour
    diff_d = np.abs(frame_gray - median_bg) * search_mask
    mask_d = (diff_d > DIFF_THRESH).astype(np.uint8) * 255
    mask_d = cv2.morphologyEx(mask_d, cv2.MORPH_CLOSE, kernel)
    mask_d = cv2.morphologyEx(mask_d, cv2.MORPH_OPEN, kernel)
    contours_d, _ = cv2.findContours(mask_d, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours_d:
        largest = max(contours_d, key=cv2.contourArea)
        if cv2.contourArea(largest) > 200:
            epsilon = 0.005 * cv2.arcLength(largest, True)
            smoothed = cv2.approxPolyDP(largest, epsilon, True)
            cv2.drawContours(panel_d, [smoothed], -1, (0, 255, 0), 3)
    # Kalman crosshair
    if kalman_initialized:
        state = kf.statePost
        kx, ky = int(state[0, 0]), int(state[1, 0])
        cv2.drawMarker(panel_d, (kx, ky), (0, 200, 255), cv2.MARKER_CROSS, 30, 3)
    panels.append(cv2.cvtColor(panel_d, cv2.COLOR_BGR2RGB))

    # --- Build figure ---
    fig, axes = plt.subplots(2, 2, figsize=(16, 10),
                             gridspec_kw={"hspace": 0.35, "wspace": 0.08})
    titles = [
        "(a) Temporal Std Heatmap",
        "(b) Median Background Subtraction",
        "(c) Start/End Frame Differencing",
        "(d) Median Diff + Kalman Filter",
    ]
    subtitles = [
        "Highlights all regions of temporal variation across video",
        "Min. enclosing circle around region differing from median background",
        "Green = diff from first frame   |   Cyan = diff from last frame",
        "Freehand contour with Kalman-filtered centroid tracking",
    ]

    for ax, panel, title, subtitle in zip(axes.flat, panels, titles, subtitles):
        ax.imshow(panel)
        ax.set_title(title, fontsize=14, fontweight="bold", pad=10,
                     fontfamily="sans-serif")
        ax.text(0.5, -0.04, subtitle, transform=ax.transAxes,
                fontsize=10, style="italic", color="#555555",
                ha="center", va="top")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#cccccc")
            spine.set_linewidth(0.5)

    fig.suptitle(
        f"Slug Detection Methods Comparison\nFrame {FRAME_IDX}  (t = {FRAME_IDX/fps:.1f} s)",
        fontsize=16, fontweight="bold", y=1.0, fontfamily="sans-serif",
    )
    plt.savefig("comparison_2x2.png", dpi=250, bbox_inches="tight",
                facecolor="white", edgecolor="none", pad_inches=0.3)
    plt.close()
    print("Written: comparison_2x2.png")


if __name__ == "__main__":
    main()
