import math
import cv2
import numpy as np


def _orientation(p1, p2):
    """Return undirected line orientation in degrees, normalized to [0, 180)."""
    dx = float(p2[0] - p1[0])
    dy = float(p2[1] - p1[1])
    return math.degrees(math.atan2(dy, dx)) % 180.0


def _included_angle(theta1, theta2):
    """Return the smaller angle between two undirected lines."""
    diff = abs(float(theta1) - float(theta2)) % 180.0
    return min(diff, 180.0 - diff)


def calculate_cra(crease, arm1_point, arm2_point):
    """
    Calculate CRA from a crease point and one point along each fabric arm.

    The points should be chosen along the centerline/direction of the fabric
    arms rather than on their outer edges.
    """
    if crease is None or arm1_point is None or arm2_point is None:
        raise ValueError("Three points are required.")

    if crease == arm1_point or crease == arm2_point:
        raise ValueError("Arm points must be different from the crease point.")

    theta1 = _orientation(crease, arm1_point)
    theta2 = _orientation(crease, arm2_point)
    angle = _included_angle(theta1, theta2)

    return float(angle), float(theta1), float(theta2)


def _distance_point_to_point(a, b):
    return math.hypot(float(a[0] - b[0]), float(a[1] - b[1]))


def _distance_point_to_segment(point, a, b):
    p = np.asarray(point, dtype=float)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    ab = b - a
    denom = np.dot(ab, ab)
    if denom == 0:
        return float(np.linalg.norm(p - a))

    t = np.dot(p - a, ab) / denom
    t = max(0.0, min(1.0, t))
    projection = a + t * ab
    return float(np.linalg.norm(p - projection))


def detect_automatic_arms(image_rgb, crease, canny_threshold=60):
    """
    Experimental automatic line detection.

    It searches for Hough line segments close to the supplied crease point and
    selects two geometrically distinct directions. This is intentionally
    conservative because background/table edges can otherwise be mistaken for
    fabric edges.
    """
    if image_rgb is None or image_rgb.ndim != 3:
        raise ValueError("Invalid image.")

    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    high = int(max(20, min(255, canny_threshold)))
    low = max(10, int(high * 0.45))

    edges = cv2.Canny(gray, low, high)

    h, w = gray.shape
    min_len = max(15, int(min(h, w) * 0.10))

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=max(15, int(min(h, w) * 0.08)),
        minLineLength=min_len,
        maxLineGap=max(5, int(min(h, w) * 0.03)),
    )

    if lines is None:
        raise ValueError("No line segments were detected.")

    candidates = []

    for item in lines[:, 0]:
        x1, y1, x2, y2 = map(int, item)
        p1 = (x1, y1)
        p2 = (x2, y2)

        length = _distance_point_to_point(p1, p2)
        if length < min_len:
            continue

        distance = _distance_point_to_segment(crease, p1, p2)

        # Only consider lines reasonably close to the crease.
        max_distance = max(30.0, min(h, w) * 0.25)
        if distance > max_distance:
            continue

        theta = _orientation(p1, p2)

        # Score long lines near the crease.
        score = (length / (distance + 10.0))

        candidates.append(
            {
                "p1": p1,
                "p2": p2,
                "length": length,
                "distance": distance,
                "theta": theta,
                "score": score,
            }
        )

    if len(candidates) < 2:
        raise ValueError(
            "Automatic mode could not find two suitable arm lines. "
            "Use Guided / Manual mode."
        )

    candidates.sort(key=lambda x: x["score"], reverse=True)

    selected = []
    angle_separation_required = 12.0

    for candidate in candidates:
        if not selected:
            selected.append(candidate)
            continue

        if all(
            _included_angle(candidate["theta"], other["theta"])
            >= angle_separation_required
            for other in selected
        ):
            selected.append(candidate)
            break

    if len(selected) < 2:
        # Fall back to the two strongest candidates.
        selected = candidates[:2]

    first, second = selected[0], selected[1]

    def nearest_endpoint(line):
        d1 = _distance_point_to_point(crease, line["p1"])
        d2 = _distance_point_to_point(crease, line["p2"])
        return line["p1"] if d1 < d2 else line["p2"]

    arm1 = nearest_endpoint(first)
    arm2 = nearest_endpoint(second)

    # Extend each detected direction away from the crease to create usable
    # points for the measurement overlay.
    def extend_from_crease(point, length):
        vx = point[0] - crease[0]
        vy = point[1] - crease[1]
        norm = math.hypot(vx, vy)
        if norm < 1:
            return point
        scale = max(1.0, length / norm)
        return (
            int(round(crease[0] + vx * scale)),
            int(round(crease[1] + vy * scale)),
        )

    arm1 = extend_from_crease(arm1, max(first["length"], min(h, w) * 0.35))
    arm2 = extend_from_crease(arm2, max(second["length"], min(h, w) * 0.35))

    angle, theta1, theta2 = calculate_cra(crease, arm1, arm2)

    # Confidence favors long, close, distinct candidate lines.
    length_score = min(
        1.0,
        (first["length"] + second["length"]) / max(1.0, min(h, w) * 1.5),
    )
    distance_score = max(
        0.0,
        1.0 - (first["distance"] + second["distance"]) / max(1.0, min(h, w)),
    )
    separation_score = min(
        1.0,
        _included_angle(theta1, theta2) / 45.0,
    )

    confidence = (
        0.40 * length_score
        + 0.35 * distance_score
        + 0.25 * separation_score
    )

    return {
        "arm1": arm1,
        "arm2": arm2,
        "theta1": theta1,
        "theta2": theta2,
        "angle": angle,
        "confidence": max(0.0, min(1.0, confidence)),
        "edges": edges,
    }


def draw_measurement(
    image_rgb,
    crease,
    arm1,
    arm2,
    angle,
    labels=True,
):
    """Draw the measured geometry on an RGB image."""
    output = image_rgb.copy()

    cv2.circle(output, tuple(map(int, crease)), 7, (255, 0, 0), -1)

    cv2.line(
        output,
        tuple(map(int, crease)),
        tuple(map(int, arm1)),
        (255, 220, 0),
        4,
        cv2.LINE_AA,
    )

    cv2.line(
        output,
        tuple(map(int, crease)),
        tuple(map(int, arm2)),
        (255, 0, 255),
        4,
        cv2.LINE_AA,
    )

    if labels:
        text = f"CRA = {angle:.2f} deg"

        cv2.putText(
            output,
            text,
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            output,
            text,
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            output,
            "Crease",
            (int(crease[0]) + 8, int(crease[1]) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

    return output
