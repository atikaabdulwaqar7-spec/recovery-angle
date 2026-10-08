
from PIL import Image
import numpy as np
import cv2

from streamlit_image_coordinates import streamlit_image_coordinates

from cra_analysis import (
    calculate_cra,
    detect_automatic_arms,
    draw_measurement,
)

st.set_page_config(
    page_title="Crease Recovery Angle Analyzer",
    page_icon="📐",
    layout="wide",
)

st.title("📐 Crease Recovery Angle Analyzer")
st.write(
    "A guided computer-vision tool for estimating the crease recovery angle "
    "(CRA) of a textile specimen from a photograph."
)

st.warning(
    "Research prototype: validate the measurement against your laboratory "
    "reference method before using it for official test results."
)

with st.sidebar:
    st.header("1. Analysis mode")
    mode = st.radio(
        "Choose how the two fabric arms are obtained:",
        ["Guided / Manual (recommended)", "Automatic (experimental)"],
    )

    st.markdown("---")
    st.header("2. Image preparation")
    st.caption(
        "The specimen should be clearly visible, preferably against a uniform "
        "contrasting background."
    )

uploaded = st.file_uploader(
    "Upload specimen photograph",
    type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"],
)

if uploaded is None:
    st.info("Upload a photograph to begin.")
    st.stop()

image = Image.open(uploaded).convert("RGB")
image_np = np.array(image)
h, w = image_np.shape[:2]

st.subheader("Original photograph")
st.image(image_np, use_container_width=True)

st.markdown("---")
st.subheader("Step 1 — Select the specimen area")

st.write(
    "Use the sliders below to crop tightly around the folded fabric specimen. "
    "Do not include large areas of the table/background."
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    x1 = st.number_input("Left (X)", 0, max(0, w - 2), 0, step=1)
with c2:
    x2 = st.number_input("Right (X)", 1, w, w, step=1)
with c3:
    y1 = st.number_input("Top (Y)", 0, max(0, h - 2), 0, step=1)
with c4:
    y2 = st.number_input("Bottom (Y)", 1, h, h, step=1)

if x2 <= x1 or y2 <= y1:
    st.error("Please make sure Right > Left and Bottom > Top.")
    st.stop()

crop = image_np[int(y1):int(y2), int(x1):int(x2)].copy()
crop_h, crop_w = crop.shape[:2]

st.image(
    crop,
    caption=f"Selected specimen area: {crop_w} × {crop_h} pixels",
    use_container_width=True,
)

st.markdown("---")

if mode == "Guided / Manual (recommended)":
    st.subheader("Step 2 — Mark the three important points")

    st.write(
        "Click the image three times in this order: "
        "**① crease point → ② point on first fabric arm → ③ point on second fabric arm**."
    )

    st.info(
        "For best accuracy, click the crease exactly where the two fabric arms "
        "meet, then click well along the center of each arm (not on the edge)."
    )

    display_width = min(850, max(350, crop_w))
    clicked = streamlit_image_coordinates(
        crop,
        width=display_width,
        key="cra_click_image",
    )

    points = st.session_state.get("cra_points", [])

    if clicked is not None:
        # Prevent repeated Streamlit reruns from adding the same click.
        display_w = clicked.get("width", display_width)
        display_h = clicked.get("height", int(crop_h * display_width / crop_w))

        sx = crop_w / max(1, display_w)
        sy = crop_h / max(1, display_h)

        px = int(round(clicked["x"] * sx))
        py = int(round(clicked["y"] * sy))
        new_point = (max(0, min(crop_w - 1, px)), max(0, min(crop_h - 1, py)))

        last = points[-1] if points else None
        if last != new_point:
            points.append(new_point)
            st.session_state["cra_points"] = points[-3:]

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Reset points"):
            st.session_state["cra_points"] = []
            st.rerun()

    points = st.session_state.get("cra_points", [])

    if points:
        st.write("Selected points:")
        for i, p in enumerate(points, start=1):
            st.write(f"**{i}.** X={p[0]}, Y={p[1]}")

    if len(points) < 3:
        st.warning(
            f"Please select {3 - len(points)} more point(s). "
            "The calculation will appear after all three points are selected."
        )
        st.stop()

    crease, arm1, arm2 = points[:3]
    angle, theta1, theta2 = calculate_cra(crease, arm1, arm2)

    annotated = draw_measurement(
        crop,
        crease,
        arm1,
        arm2,
        angle,
        labels=True,
    )

    st.markdown("---")
    st.subheader("Result")

    col_a, col_b = st.columns([1.5, 1])

    with col_a:
        st.image(annotated, caption="Measurement overlay", use_container_width=True)

    with col_b:
        st.metric("Crease Recovery Angle", f"{angle:.2f}°")
        st.write(f"Arm 1 orientation: **{theta1:.2f}°**")
        st.write(f"Arm 2 orientation: **{theta2:.2f}°**")
        st.success("Manual geometry selected successfully.")

        ok, encoded = cv2.imencode(
            ".png", cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
        )
        if ok:
            st.download_button(
                "Download annotated result",
                data=encoded.tobytes(),
                file_name="cra_result.png",
                mime="image/png",
            )

else:
    st.subheader("Step 2 — Automatic arm detection")
    st.info(
        "Automatic mode is experimental. Because textile photographs can contain "
        "shadows, folds, table edges and other strong lines, the automatic result "
        "should always be checked visually."
    )

    center_x = st.slider(
        "Estimated crease X",
        0,
        max(1, crop_w - 1),
        crop_w // 2,
    )
    center_y = st.slider(
        "Estimated crease Y",
        0,
        max(1, crop_h - 1),
        crop_h // 2,
    )
    crease = (center_x, center_y)

    sensitivity = st.slider(
        "Edge sensitivity",
        20,
        150,
        60,
        help="Higher values require stronger edges.",
    )

    try:
        result = detect_automatic_arms(
            crop,
            crease,
            canny_threshold=sensitivity,
        )

        annotated = draw_measurement(
            crop,
            crease,
            result["arm1"],
            result["arm2"],
            result["angle"],
            labels=True,
        )

        col_a, col_b = st.columns([1.5, 1])

        with col_a:
            st.image(
                annotated,
                caption="Automatic detection overlay",
                use_container_width=True,
            )

        with col_b:
            st.metric("Estimated CRA", f'{result["angle"]:.2f}°')
            st.write(f'Arm 1 orientation: **{result["theta1"]:.2f}°**')
            st.write(f'Arm 2 orientation: **{result["theta2"]:.2f}°**')
            st.write(f'Candidate line confidence: **{result["confidence"]:.0%}**')

            if result["confidence"] < 0.55:
                st.warning(
                    "Low confidence. Use Guided / Manual mode for the final measurement."
                )
            else:
                st.success("Automatic candidate geometry found.")

            ok, encoded = cv2.imencode(
                ".png", cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            )
            if ok:
                st.download_button(
                    "Download annotated result",
                    data=encoded.tobytes(),
                    file_name="cra_automatic_result.png",
                    mime="image/png",
                )

    except Exception as exc:
        st.error(
            "Automatic detection could not find two reliable fabric-arm lines. "
            "Please switch to Guided / Manual mode."
        )
        st.caption(str(exc))

st.markdown("---")
st.caption(
    "Crease Recovery Angle Analyzer — image-analysis research prototype."
)
