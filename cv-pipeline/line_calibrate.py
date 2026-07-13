#!/usr/bin/env python3
"""Classical fallback calibration — white court lines via Hough.

When the YOLO net/serve-line classes fail (angle not in training data), find
the court's white lines directly: white mask -> HoughLinesP -> cluster into
the two horizontal court lines (near serve line, far serve line) + the centre
line, and build the homography from their intersections.

Debug: python line_calibrate.py <frame.jpg> <out.jpg>  draws everything found.
"""
import sys
import cv2
import numpy as np


def white_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # white: low saturation, high value
    return cv2.inRange(hsv, (0, 0, 165), (180, 90, 255))


def find_lines(img, debug=None):
    H, W = img.shape[:2]
    mask = white_mask(img)
    # only look at the court surface (lower 2/3), ignore lights/structure above
    mask[: int(H * 0.33), :] = 0
    lines = cv2.HoughLinesP(mask, 1, np.pi / 180, threshold=60,
                            minLineLength=W * 0.10, maxLineGap=W * 0.02)
    horiz, vert = [], []
    if lines is None:
        return horiz, vert
    for l in lines.reshape(-1, 4):
        x1, y1, x2, y2 = (float(v) for v in l)
        dx, dy = x2 - x1, y2 - y1
        ang = abs(np.degrees(np.arctan2(dy, dx)))
        if ang < 12 or ang > 168:
            horiz.append((x1, y1, x2, y2))
        elif 55 < ang < 125:
            vert.append((x1, y1, x2, y2))
    return horiz, vert


def cluster_horiz(horiz, H):
    """Group horizontal segments by y, merge each cluster into one long line."""
    if not horiz:
        return []
    segs = sorted(horiz, key=lambda s: (s[1] + s[3]) / 2)
    clusters = []
    for s in segs:
        yc = (s[1] + s[3]) / 2
        if clusters and abs(yc - clusters[-1]["y"]) < H * 0.035:
            c = clusters[-1]
            c["segs"].append(s)
            c["y"] = np.mean([(t[1] + t[3]) / 2 for t in c["segs"]])
        else:
            clusters.append({"y": yc, "segs": [s]})
    out = []
    for c in clusters:
        xs = [p for s in c["segs"] for p in (s[0], s[2])]
        pts = []
        for s in c["segs"]:
            pts += [(s[0], s[1]), (s[2], s[3])]
        pts = np.array(pts)
        # fit y = a*x + b across the cluster for a stable long line
        a, b = np.polyfit(pts[:, 0], pts[:, 1], 1)
        x_lo, x_hi = min(xs), max(xs)
        out.append({"y": c["y"], "x_lo": x_lo, "x_hi": x_hi, "a": a, "b": b,
                    "width": x_hi - x_lo})
    return out


def line_homography(img, debug_path=None):
    """Homography from the two widest horizontal court lines.

    Camera behind one baseline (our capture spec): the widest low line is the
    NEAR serve line (world y=3), the widest line above it is the FAR serve
    line (world y=17). Their endpoints hit the side walls at world x=0 / x=10.
    """
    H_img, W_img = img.shape[:2]
    horiz, vert = find_lines(img)
    clusters = [c for c in cluster_horiz(horiz, H_img) if c["width"] > W_img * 0.30]

    if debug_path:
        vis = img.copy()
        for c in clusters:
            p1 = (int(c["x_lo"]), int(c["a"] * c["x_lo"] + c["b"]))
            p2 = (int(c["x_hi"]), int(c["a"] * c["x_hi"] + c["b"]))
            cv2.line(vis, p1, p2, (0, 255, 255), 3)
            cv2.putText(vis, f"w={c['width']:.0f} y={c['y']:.0f}", (p1[0], p1[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        for s in vert:
            cv2.line(vis, (int(s[0]), int(s[1])), (int(s[2]), int(s[3])), (255, 120, 0), 2)
        cv2.imwrite(debug_path, vis)

    if len(clusters) < 2:
        return None, f"lines: found {len(clusters)} wide horizontals, need 2"

    clusters.sort(key=lambda c: c["y"])          # top of image first = far
    far, near = clusters[0], clusters[-1]

    def ends(c, wy):
        y_lo = c["a"] * c["x_lo"] + c["b"]
        y_hi = c["a"] * c["x_hi"] + c["b"]
        return [([c["x_lo"], y_lo], [0, wy]), ([c["x_hi"], y_hi], [10, wy])]

    pairs = ends(far, 17) + ends(near, 3)
    img_pts = np.float32([p[0] for p in pairs])
    world_pts = np.float32([p[1] for p in pairs])
    Hm = cv2.getPerspectiveTransform(img_pts, world_pts)
    return Hm, f"ok (2 court lines, far y={far['y']:.0f} near y={near['y']:.0f})"


if __name__ == "__main__":
    img = cv2.imread(sys.argv[1])
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/line_cal_debug.jpg"
    Hm, msg = line_homography(img, debug_path=out)
    print(msg)
    if Hm is not None:
        # reproject the court to verify visually
        vis = cv2.imread(out)
        Hinv = np.linalg.inv(Hm)
        def w2i(x, y):
            p = cv2.perspectiveTransform(np.float32([[[x, y]]]), Hinv)[0][0]
            return int(round(p[0])), int(round(p[1]))
        for a, b in [((0,0),(10,0)),((0,20),(10,20)),((0,0),(0,20)),((10,0),(10,20)),
                     ((0,10),(10,10)),((0,3),(10,3)),((0,17),(10,17)),((5,3),(5,17))]:
            cv2.line(vis, w2i(*a), w2i(*b), (60, 120, 255), 2)
        cv2.imwrite(out, vis)
        print("debug + reprojected court ->", out)
