# Crease Recovery Angle Analyzer

A Streamlit web application for estimating **Crease Recovery Angle (CRA)** from a textile specimen image using computer vision.

## Features

- Upload JPG, JPEG, PNG, BMP, TIF or TIFF images
- Automatic image preprocessing
- Threshold-based textile/background segmentation
- Specimen contour detection
- Estimation of the two fabric-arm orientations
- Automatic CRA calculation
- Annotated result image
- Rough confidence indicator
- Downloadable annotated image
- Runs locally or on Streamlit Community Cloud

## Important scientific note

This repository is a **research/prototype image-analysis system**. The current algorithm is intentionally general-purpose and should not be treated as a validated replacement for a textile testing standard.

For laboratory or publication use, the algorithm should be validated against the exact test method being followed, including:

- specimen dimensions
- folding procedure
- recovery time
- camera position
- lighting
- background
- scale/calibration
- angle definition
- manual/reference measurements

The applicable standard should be specified before final validation.

## Project structure

```text
crease-recovery-angle/
│
├── app.py
├── cra_analysis.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Run locally

### 1. Install Python

Python 3.10 or newer is recommended.

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Streamlit

```bash
streamlit run app.py
```

The application will open in your browser.

## GitHub

Create a new GitHub repository and upload:

```text
app.py
cra_analysis.py
requirements.txt
README.md
.gitignore
```

Or from a terminal:

```bash
git init
git add .
git commit -m "Initial crease recovery angle analyzer"
git branch -M main
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

## Deploy on Streamlit Community Cloud

1. Push the project to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app.
4. Select your GitHub repository.
5. Select the `main` branch.
6. Set the main file to:

```text
app.py
```

7. Deploy.

Streamlit will install the packages listed in `requirements.txt`.

## Recommended image acquisition

For more reliable results:

- Place the specimen on a matte, uniform background.
- Use diffuse lighting.
- Avoid strong shadows.
- Keep the camera perpendicular to the specimen.
- Keep camera distance and resolution consistent.
- Keep the specimen fully visible.
- Use the same recovery time for every measurement.

## Future improvements

The next version can add:

1. Manual selection of the crease point.
2. Automatic perspective correction.
3. Camera calibration.
4. A physical reference scale.
5. Region-of-interest selection.
6. Better fabric/background segmentation.
7. More robust line fitting.
8. Batch image analysis.
9. CSV/Excel export.
10. Measurement history.
11. Experimental/reference CRA comparison.
12. Accuracy, repeatability and reproducibility statistics.
13. Automatic image-quality warnings.
14. Support for a specific ASTM/ISO test workflow.

## License

Add the license appropriate for your project before publishing the repository.
