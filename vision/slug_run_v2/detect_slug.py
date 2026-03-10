"""
Detect and outline the slug using background subtraction + Kalman filtering.

Strategy:
  - Median background from the same video (slug averages out since it moves).
  - Per-frame diff from median, masked to tube ROI, reveals where the slug is.
  - Kalman filter smooths the centroid tracking (slug moves, doesn't teleport).
  - Freehand contour drawn around the detected slug region.

Outputs: overlay_detected.mp4
"""

import cv2
import numpy as np


VIDEO = "slug_run_30s.mp4"
OUT = "."
DIFF_THRESH = 15.0


def make_kalman():
    """2D position + velocity Kalman filter."""
    kf = cv2.KalmanFilter(4, 2)  # state: [x, y, vx, vy], measurement: [x, y]
    dt = 1.0
    kf.transitionMatrix = np.array([
        [1, 0, dt, 0],
        [0, 1, 0, dt],
        [0, 0, 1,  0],
        [0, 0, 0,  1],
    ], dtype=np.float32)
    kf.measurementMatrix = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
    ], dtype=np.float32)
    kf.processNoiseCov = np.eye(4, dtype=np.float32) * 1.0
    kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * 10.0
    kf.errorCovPost = np.eye(4, dtype=np.float32) * 100.0
    return kf


def main():
    import os
    os.makedirs(OUT, exist_ok=True)

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

    h, w = frames_gray[0].shape
    n = len(frames_gray)
    print(f"{n} frames, {w}x{h} @ {fps:.0f} fps")

    # Background from first and last 3 seconds (slug-free)
    bg_frames_count = int(3 * fps)
    bg_subset = frames_gray[:bg_frames_count] + frames_gray[-bg_frames_count:]
    bg_stack = np.array(bg_subset)
    median_bg = np.median(bg_stack, axis=0)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))

    # Kalman filter for slug centroid
    kf = make_kalman()
    kalman_initialized = False

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(f"{OUT}/overlay_detected.mp4", fourcc, fps, (w, h))

    for i, (bgr, gray) in enumerate(zip(frames_bgr, frames_gray)):
        frame_out = bgr.copy()

        # Diff from background
        diff = np.abs(gray - median_bg)
        detection_mask = (diff > DIFF_THRESH).astype(np.uint8) * 255
        detection_mask = cv2.morphologyEx(detection_mask, cv2.MORPH_CLOSE, kernel)
        detection_mask = cv2.morphologyEx(detection_mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(detection_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        measured_cx, measured_cy = None, None
        best_contour = None

        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            if area > 200:
                best_contour = largest
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    measured_cx = M["m10"] / M["m00"]
                    measured_cy = M["m01"] / M["m00"]

        # Kalman update
        if measured_cx is not None:
            measurement = np.array([[np.float32(measured_cx)],
                                     [np.float32(measured_cy)]])
            if not kalman_initialized:
                kf.statePost = np.array([
                    [np.float32(measured_cx)],
                    [np.float32(measured_cy)],
                    [np.float32(0)],
                    [np.float32(0)],
                ])
                kalman_initialized = True

            kf.predict()
            kf.correct(measurement)
        elif kalman_initialized:
            kf.predict()

        # Draw
        if best_contour is not None:
            # Smooth contour outline
            epsilon = 0.005 * cv2.arcLength(best_contour, True)
            smoothed = cv2.approxPolyDP(best_contour, epsilon, True)
            cv2.drawContours(frame_out, [smoothed], -1, (0, 255, 0), 3)

        if kalman_initialized:
            # Kalman-filtered centroid
            state = kf.statePost
            kx, ky = int(state[0, 0]), int(state[1, 0])
            # Crosshair at filtered position
            cv2.drawMarker(frame_out, (kx, ky), (0, 200, 255),
                           cv2.MARKER_CROSS, 30, 2)
            cv2.putText(frame_out, "SLUG", (kx - 30, ky - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        # Info
        mean_diff = np.mean(diff)
        cv2.putText(frame_out, f"Frame {i:3d}  mean_diff={mean_diff:.1f}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        out.write(frame_out)

    out.release()
    print(f"Written: {OUT}/overlay_detected.mp4")


if __name__ == "__main__":
    main()
