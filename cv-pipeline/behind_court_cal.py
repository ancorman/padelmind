#!/usr/bin/env python3
"""Auto-calibration v2 — the standard "phone behind the court" view.

At this angle the near serve line sits behind the camera, so the 2-line
calibration can't work. But four world-known LINES are visible: the far serve
line (y=17), the far baseline (y=20), and both floor-sidewall junctions
(x=0, x=10) running the full court depth. A point on a known line gives one
linear constraint on the homography, so we sample many points along each and
solve by least-squares DLT. The sideline samples in the NEAR half are what
keep the solution stable where the ball actually bounces.

Debug: python behind_court_cal.py <frame.jpg> <out.jpg>
"""
import sys
import cv2
import numpy as np

FLOOR_LO = (95, 90, 140)     # court blue (HSV)
FLOOR_HI = (125, 255, 255)
WHITE_S_MAX, WHITE_V_MIN = 95, 185


def floor_mask(img):
    """Returns (mask, far_top, near_top): the merged court-floor mask plus the
    image-rows where the far and near floor blobs begin. The net mesh splits
    the floor in two; blue tarps/ceiling match the colour but sit in the top
    quarter, so they're excluded by position."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, FLOOR_LO, FLOOR_HI)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None, 0, 0
    areas = stats[1:, cv2.CC_STAT_AREA]
    tops = stats[1:, cv2.CC_STAT_TOP]
    ok = (areas >= 0.04 * areas.max()) & (tops > img.shape[0] * 0.25)
    keep = 1 + np.where(ok)[0]
    if len(keep) == 0:
        return None, 0, 0
    near_top = int(tops[np.argmax(areas)])                 # biggest blob = near half
    far_top = int(tops[ok].min())
    return np.isin(lab, keep).astype(np.uint8) * 255, far_top, near_top


def fit_line_ransac(pts, iters=300, tol=4.0):
    """Robust 2D line fit -> (point, direction). pts: Nx2 float."""
    pts = np.asarray(pts, np.float64)
    if len(pts) < 2:
        return None
    best, best_n = None, -1
    rng = np.random.default_rng(7)
    for _ in range(iters):
        i, j = rng.choice(len(pts), 2, replace=False)
        p, q = pts[i], pts[j]
        d = q - p
        L = np.hypot(*d)
        if L < 1e-6:
            continue
        d = d / L
        r = pts - p
        dist = np.abs(r[:, 0] * d[1] - r[:, 1] * d[0])
        n = int(np.sum(dist < tol))
        if n > best_n:
            best_n, best = n, (p, d, dist < tol)
    p, d, inl = best
    P = pts[inl]
    c = P.mean(0)
    u, s, vt = np.linalg.svd(P - c)
    return c, vt[0]


def sample_line(line, y_range=None, x_range=None, n=8):
    """n points along a fitted line clipped to an image-coordinate range."""
    c, d = line
    ts = np.linspace(-2000, 2000, 4001)
    pts = c[None] + ts[:, None] * d[None]
    ok = np.ones(len(pts), bool)
    if y_range:
        ok &= (pts[:, 1] >= y_range[0]) & (pts[:, 1] <= y_range[1])
    if x_range:
        ok &= (pts[:, 0] >= x_range[0]) & (pts[:, 0] <= x_range[1])
    pts = pts[ok]
    if len(pts) < n:
        return pts
    idx = np.linspace(0, len(pts) - 1, n).astype(int)
    return pts[idx]


def behind_court_homography(img, debug_path=None):
    H_img, W_img = img.shape[:2]
    fm, far_top, near_top = floor_mask(img)
    if fm is None:
        return None, "no floor region"
    top = far_top

    # --- far baseline (y=20): topmost floor pixel per column, robust fit ---
    base_pts = []
    for x in range(int(W_img * 0.15), int(W_img * 0.85), 8):
        col = np.where(fm[:, x] > 0)[0]
        if len(col):
            base_pts.append((x, col.min()))
    base = fit_line_ransac(base_pts, tol=3.0)

    # --- side junctions (x=0 / x=10): left/right-most floor pixel per row ---
    left_pts, right_pts = [], []
    for y in range(top + 20, H_img - 4, 6):
        row = np.where(fm[y, :] > 0)[0]
        if len(row) > W_img * 0.2:
            left_pts.append((row.min(), y))
            right_pts.append((row.max(), y))
    left = fit_line_ransac(left_pts, tol=5.0)
    right = fit_line_ransac(right_pts, tol=5.0)

    # --- far serve line (y=17): a BLUISH white on this floor (S~125, V~245 vs
    # floor V<=225), so value is the separator, not saturation ---
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    white = ((hsv[:, :, 1] < 160) & (hsv[:, :, 2] > 232)).astype(np.uint8) * 255
    white[fm == 0] = 0
    # serve line lives in the FAR blob only — stop well before the near blob
    # (morphology swallows the net band's antialiased top rows into the floor)
    strip_lo, strip_hi = top + 2, max(top + 10, near_top - 16)
    serve_pts = []
    for x in range(int(W_img * 0.2), int(W_img * 0.8), 6):
        col = np.where(white[strip_lo:strip_hi, x] > 0)[0]
        if len(col):
            serve_pts.append((x, strip_lo + int(np.median(col))))
    serve = fit_line_ransac(serve_pts, tol=3.0) if len(serve_pts) > 10 else None

    if debug_path:
        vis = img.copy()
        vis[fm > 0] = vis[fm > 0] * 0.75 + np.array([40, 20, 0]) * 0.25
        for line, col in [(base, (0, 0, 255)), (left, (255, 120, 0)),
                          (right, (255, 120, 0)), (serve, (0, 255, 255))]:
            if line is None:
                continue
            c, d = line
            p1 = tuple((c - 1400 * d).astype(int))
            p2 = tuple((c + 1400 * d).astype(int))
            cv2.line(vis, p1, p2, col, 2)
        cv2.imwrite(debug_path, vis)

    missing = [n for n, l in [("baseline", base), ("left", left),
                              ("right", right), ("serve", serve)] if l is None]
    if missing:
        return None, f"missing lines: {missing}"

    # --- net posts (y=10): the near half has no floor line of its own, so
    # anchor it via the net band. Its endpoints sit atop the posts at (0,10)
    # and (10,10); an image-vertical drop from each endpoint to the sideline
    # junction lands ~on the post base (camera is near-level, error is small).
    white_full = ((hsv[:, :, 1] < WHITE_S_MAX) & (hsv[:, :, 2] > 200)).astype(np.uint8) * 255
    band_lo = int(serve[0][1] + H_img * 0.02)
    band_hi = int(serve[0][1] + H_img * 0.20)
    band_pts = []
    for x in range(int(W_img * 0.05), int(W_img * 0.95), 8):
        col = np.where(white_full[band_lo:band_hi, x] > 0)[0]
        if len(col):
            band_pts.append((x, band_lo + int(np.median(col))))
    post_pts = []
    if len(band_pts) > W_img * 0.5 / 8:                    # band spans most of the court
        band = fit_line_ransac(band_pts, tol=4.0)
        if band is not None:
            bxs = [p[0] for p in band_pts]
            for bx, junction in ((min(bxs), left), (max(bxs), right)):
                c, d = junction
                if abs(d[0]) < 1e-9:                        # junction is image-vertical
                    post_pts.append((c[0], bx and c[1]))
                    continue
                # x = c.x + t*d.x = bx  ->  t; y on the junction at that x
                t = (bx - c[0]) / d[0]
                post_pts.append((bx, c[1] + t * d[1]))

    # --- DLT with point-on-line constraints ---
    # x-constraint (world x = X):  a.p - X (c.p) = 0
    # y-constraint (world y = Y):  b.p - Y (c.p) = 0
    T = np.array([[2.0 / W_img, 0, -1], [0, 2.0 / H_img, -1], [0, 0, 1]])  # conditioning
    rows = []
    def add(pts, kind, val):
        for p in pts:
            ph = T @ np.array([p[0], p[1], 1.0])
            if kind == "x":
                rows.append(np.concatenate([ph, np.zeros(3), -val * ph]))
            else:
                rows.append(np.concatenate([np.zeros(3), ph, -val * ph]))

    add(sample_line(serve, x_range=(W_img * 0.15, W_img * 0.85), n=6), "y", 17.0)
    add(sample_line(base, x_range=(W_img * 0.15, W_img * 0.85), n=6), "y", 20.0)
    add(sample_line(left, y_range=(top + 10, H_img - 5), n=10), "x", 0.0)
    add(sample_line(right, y_range=(top + 10, H_img - 5), n=10), "x", 10.0)
    if len(post_pts) == 2:
        add(post_pts, "y", 10.0)                            # net posts pin the near half
    else:
        return None, "net band not found — no y-anchor for the near half"

    A = np.array(rows)
    _, _, vt = np.linalg.svd(A)
    Hn = vt[-1].reshape(3, 3)
    Hm = Hn @ T                       # image -> world
    Hm /= Hm[2, 2]

    # sanity: image centre-bottom should project inside the near half
    probe = cv2.perspectiveTransform(np.float32([[[W_img / 2, H_img * 0.9]]]), Hm)[0][0]
    if not (-3 < probe[0] < 13 and -5 < probe[1] < 12):
        return None, f"solve unstable (probe -> {probe.round(1)})"
    return Hm, "ok (behind-court DLT: serve+baseline+2 sidelines)"


if __name__ == "__main__":
    img = cv2.imread(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/bc_cal.jpg"
    Hm, msg = behind_court_homography(img, debug_path=out)
    print(msg)
    if Hm is not None:
        vis = cv2.imread(out)
        Hinv = np.linalg.inv(Hm)
        def w2i(x, y):
            p = cv2.perspectiveTransform(np.float32([[[x, y]]]), Hinv)[0][0]
            return int(round(p[0])), int(round(p[1]))
        court = [((0, 0), (10, 0)), ((0, 20), (10, 20)), ((0, 0), (0, 20)),
                 ((10, 0), (10, 20)), ((0, 10), (10, 10)), ((0, 3), (10, 3)),
                 ((0, 17), (10, 17)), ((5, 10), (5, 17)), ((5, 3), (5, 10))]
        for a, b in court:
            cv2.line(vis, w2i(*a), w2i(*b), (60, 120, 255), 2)
        cv2.imwrite(out, vis)
        print("reprojected court ->", out)
