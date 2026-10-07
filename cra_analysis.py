import cv2
import numpy as np


def _odd(value: int) -> int:
    value = int(value)
    return value if value % 2 == 1 else value + 1


def _segment(gray, threshold_mode="Auto"):
    """Create a binary specimen mask using several simple segmentation strategies."""
    if threshold_mode == "Adaptive":
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            51,
            5,
        )
    else:
        _, binary = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

    # We don't know whether the fabric or background is brighter.
    # Prefer the mask whose largest meaningful component is not the whole image.
    candidates = [binary, cv2.bitwise_not(binary)]

    best = None
    best_score = -1

    h, w = gray.shape
    image_area = h * w

    for mask in candidates:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask, connectivity=8
        )

        score = 0
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < image_area * 0.005:
                continue
            if area > image_area * 0.95:
                continue
            score = max(score, area)

        if score > best_score:
            best_score = score
            best = mask

    if best is None:
        best = binary

    kernel = np.ones((5, 5), np.uint8)
    best = cv2.morphologyEx(best, cv2.MORPH_CLOSE, kernel, iterations=2)
    best = cv2.morphologyEx(best, cv2.MORPH_OPEN, kernel, iterations=1)

    return best


def _largest_contours(mask, min_area):
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contours = [c for c in contours if cv2.contourArea(c) >= min_area]
    contours.sort(key=cv2.contourArea, reverse=True)
    return contours


def _pca_angle(points):
    points = np.asarray(points, dtype=np.float32)
    if len(points) < 2:
        raise ValueError("Not enough points for orientation estimation.")

    mean = points.mean(axis=0)
    centered = points - mean

    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    direction = vt[0]

    angle = np.degrees(np.arctan2(direction[1], direction[0]))
    return angle, mean


def _normalize_line_angle(angle):
    # Line orientation is undirected: 0° and 180° are equivalent.
    angle = angle % 180.0
    return angle


def _acute_difference(a, b):
    diff = abs(a - b) % 180.0
    return min(diff, 180.0 - diff)


def _split_points(points, crease_point, side):
    x0, y0 = crease_point
    pts = np.asarray(points)

    if side == "left":
        return pts[pts[:, 0] < x0]
    return pts[pts[:, 0] >= x0]


def analyze_crease_image(
    image_rgb,
    threshold_mode="Auto",
    blur_size=5,
    min_area=1000,
    line_percent=0.50,
):
    """
    Estimate CRA from a textile image.

    This is a general-purpose image-analysis prototype. It assumes the specimen
    forms two visible arms around a central crease. For laboratory-grade results,
    the image setup and algorithm should be calibrated against the applicable
    textile standard and reference measurements.
    """
    if image_rgb is None or image_rgb.ndim != 3:
        raise ValueError("Invalid RGB image.")

    original = image_rgb.copy()
    gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)

    blur_size = max(1, min(15, int(blur_size)))
    blur_size = _odd(blur_size)

    if blur_size > 1:
        gray = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)

    mask = _segment(gray, threshold_mode)
    contours = _largest_contours(mask, min_area)

    if not contours:
        raise ValueError(
            "No sufficiently large specimen region was detected. "
            "Try a clearer image or reduce the minimum contour area."
        )

    # Use the largest contour as the primary specimen.
    contour = contours[0]
    pts = contour.reshape(-1, 2)

    if len(pts) < 10:
        raise ValueError("The detected specimen contour is too small.")

    # Estimate a central crease point using the contour's center.
    moments = cv2.moments(contour)
    if moments["m00"] != 0:
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
    else:
        cx, cy = np.mean(pts, axis=0)

    crease_point = (int(round(cx)), int(round(cy)))

    left = _split_points(pts, crease_point, "left")
    right = _split_points(pts, crease_point, "right")

    # If one side is too small, fall back to an x-based split at the median.
    if len(left) < 10 or len(right) < 10:
        median_x = np.median(pts[:, 0])
        crease_point = (int(round(median_x)), int(round(cy)))
        left = _split_points(pts, crease_point, "left")
        right = _split_points(pts, crease_point, "right")

    if len(left) < 10 or len(right) < 10:
        raise ValueError(
            "The algorithm could not identify two distinct fabric arms."
        )

    # Prefer points farther from the estimated crease because they generally
    # represent the arm direction more clearly than the curved crease region.
    x0, y0 = crease_point

    def select_arm(points):
        p = np.asarray(points)
        distances = np.sqrt((p[:, 0] - x0) ** 2 + (p[:, 1] - y0) ** 2)
        cutoff = np.quantile(distances, max(0.0, min(1.0, 1.0 - line_percent)))
        selected = p[distances >= cutoff]
        return selected if len(selected) >= 5 else p

    left_fit = select_arm(left)
    right_fit = select_arm(right)

    theta1_raw, left_center = _pca_angle(left_fit)
    theta2_raw, right_center = _pca_angle(right_fit)

    theta1 = _normalize_line_angle(theta1_raw)
    theta2 = _normalize_line_angle(theta2_raw)

    angle = _acute_difference(theta1, theta2)

    # A rough confidence score based on arm point counts and separation.
    point_score = min(1.0, (len(left_fit) + len(right_fit)) / 200.0)
    separation = abs(theta1 - theta2)
    separation_score = min(1.0, separation / 30.0) if separation > 0 else 0.0
    confidence = 0.55 * point_score + 0.45 * separation_score

    # Annotated RGB image.
    annotated = original.copy()

    # Specimen contour.
    cv2.drawContours(annotated, [contour], -1, (0, 255, 0), 2)

    # Crease point.
    cv2.circle(annotated, crease_point, 8, (255, 0, 0), -1)

    # Draw fitted lines from the crease toward each arm center.
    def draw_arm(center, point_color):
        center = np.asarray(center, dtype=float)
        start = np.asarray(crease_point, dtype=float)

        vector = center - start
        norm = np.linalg.norm(vector)
        if norm < 1:
            return

        unit = vector / norm
        length = max(80.0, norm * 1.8)

        p1 = start
        p2 = start + unit * length

        cv2.line(
            annotated,
            tuple(np.round(p1).astype(int)),
            tuple(np.round(p2).astype(int)),
            point_color,
            4,
            cv2.LINE_AA,
        )

    draw_arm(left_center, (255, 255, 0))
    draw_arm(right_center, (255, 0, 255))

    cv2.putText(
        annotated,
        f"CRA: {angle:.2f} deg",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        annotated,
        f"CRA: {angle:.2f} deg",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )

    return {
        "angle": float(angle),
        "theta1": float(theta1),
        "theta2": float(theta2),
        "confidence": float(max(0.0, min(1.0, confidence))),
        "crease_point": crease_point,
        "annotated": annotated,
        "mask": mask,
    }
