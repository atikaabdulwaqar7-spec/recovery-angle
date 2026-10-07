import streamlit as st
from PIL import Image
import numpy as np
import cv2

from cra_analysis import analyze_crease_image

st.set_page_config(
    page_title="Crease Recovery Angle Analyzer",
    page_icon="📐",
    layout="wide"
)

st.title("📐 Crease Recovery Angle Analyzer")
st.write(
    "Upload an image of a creased textile specimen. The application detects the two "
    "fabric arms and estimates the crease recovery angle using computer vision."
)

with st.sidebar:
    st.header("Analysis Settings")
    threshold_mode = st.selectbox(
        "Segmentation method",
        ["Auto", "Otsu", "Adaptive"]
    )
    blur_size = st.slider("Noise reduction", 1, 15, 5, step=2)
    min_area = st.slider("Minimum contour area", 100, 10000, 1000, step=100)
    line_percent = st.slider(
        "Line fitting region (%)",
        20, 80, 50,
        help="Percentage of each detected arm used for fitting its main direction."
    )

    st.markdown("---")
    st.info(
        "For best results, photograph the specimen from directly above using a "
        "uniform, contrasting background and avoid shadows."
    )

uploaded = st.file_uploader(
    "Upload specimen image",
    type=["jpg", "jpeg", "png", "bmp", "tif", "tiff"]
)

if uploaded is None:
    st.info("Upload an image to begin the analysis.")
    st.stop()

image = Image.open(uploaded).convert("RGB")
image_np = np.array(image)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Original image")
    st.image(image, use_container_width=True)

try:
    result = analyze_crease_image(
        image_np,
        threshold_mode=threshold_mode,
        blur_size=blur_size,
        min_area=min_area,
        line_percent=line_percent / 100.0
    )

    with col2:
        st.subheader("Detected geometry")
        st.image(result["annotated"], use_container_width=True)

    st.markdown("---")
    st.subheader("Result")

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        "Crease Recovery Angle",
        f'{result["angle"]:.2f}°'
    )

    metric2.metric(
        "Left arm orientation",
        f'{result["theta1"]:.2f}°'
    )

    metric3.metric(
        "Right arm orientation",
        f'{result["theta2"]:.2f}°'
    )

    if result["confidence"] >= 0.75:
        st.success(f'Analysis confidence: {result["confidence"]:.0%}')
    elif result["confidence"] >= 0.50:
        st.warning(
            f'Analysis confidence: {result["confidence"]:.0%}. '
            "Consider improving lighting/background or adjusting the specimen crop."
        )
    else:
        st.error(
            f'Low analysis confidence: {result["confidence"]:.0%}. '
            "Try a clearer image with a uniform background."
        )

    with st.expander("Processing details"):
        st.write(
            "The algorithm converts the image to grayscale, segments the specimen, "
            "identifies the main fabric arms, fits their orientations, and calculates "
            "the included angle."
        )
        st.write(f'Image size: {image_np.shape[1]} × {image_np.shape[0]} pixels')
        st.write(f'Estimated crease point: {result["crease_point"]}')

    st.download_button(
        "Download annotated image",
        data=cv2.imencode(
            ".png",
            cv2.cvtColor(result["annotated"], cv2.COLOR_RGB2BGR)
        )[1].tobytes(),
        file_name="cra_annotated_result.png",
        mime="image/png"
    )

except Exception as exc:
    st.error("The image could not be analyzed.")
    st.exception(exc)

st.markdown("---")
st.caption(
    "Crease Recovery Angle Analyzer — research/prototype software. "
    "Validate the algorithm against your laboratory reference method before using "
    "it for official textile test results."
)
