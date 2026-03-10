# slug_run_v2

Slug detection via background subtraction from slug-free frames, with a horizontal morphological close to bridge gaps where the channel narrows and a convex hull merge to unify fragmented contour detections into a single slug region. A Kalman filter with low measurement noise tracks the centroid smoothly while staying responsive to rapid shifts in slug position.
