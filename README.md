Crease Recovery Angle Analyzer — V2

A Streamlit research prototype for estimating the Crease Recovery Angle (CRA) of textile specimens from photographs.

Why V2 is different

The first version tried to identify the specimen from the whole photograph using the largest image contour. In laboratory photographs this can fail because the table, shadows, background boundaries, or other objects may create larger contours than the actual textile specimen.

V2 therefore uses a guided measurement workflow:

Upload the photograph.

Crop tightly around the specimen.

Click the crease point.

Click one point along the first fabric arm.

Click one point along the second fabric arm.

The application calculates the angle between those two directions.

Download the annotated result.

There is also an Automatic (experimental) mode, but Guided / Manual mode is recommended for research measurements.

Project structure

crease-recovery-angle/
│
├── app.py
├── cra_analysis.py
├── requirements.txt
├── README.md
└── .gitignore

Main file

The Streamlit entry point is:

app.py

Deploy app.py as the main file in Streamlit Community Cloud.

Local installation

python -m venv .venv

Windows:

.venv\Scripts\activate

macOS/Linux:

source .venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Run:

streamlit run app.py

Streamlit Community Cloud

When Streamlit asks for the Main file path, select:

app.py

Do not select cra_analysis.py.

How to measure a specimen

Step 1 — Photograph

Use a stable camera position, preferably perpendicular to the specimen/test plane.

Avoid:

strong shadows

reflective surfaces

patterned backgrounds

severe perspective distortion

motion blur

Step 2 — Crop

Crop tightly around the specimen. The crop should contain the complete folded fabric and as little background as possible.

Step 3 — Select three points

Click:

1. Crease point
2. Point along fabric arm 1
3. Point along fabric arm 2

The application calculates the included angle between the two directions.

Important

Click the centerline of each fabric arm, not its outer edge. If the fabric is thick or irregular, repeat the measurement using consistent point-selection rules.

Scientific validation

This application is not automatically compliant with any particular ASTM or ISO method.

Before using it for a thesis, paper, laboratory report, or standard testing, specify the exact method being followed and validate the software against reference measurements.

A useful validation dataset should contain multiple specimens covering the expected range of CRA values.

Compare:

manual/reference CRA

image-analysis CRA

absolute error

mean absolute error

standard deviation

repeatability

inter-observer variation, where applicable

Recommended next development

For a fully automatic laboratory system, the next version should incorporate:

fixed camera geometry

perspective correction

controlled lighting

specimen fixture detection

automatic crease localization

fabric-arm centerline extraction

automatic quality checks

calibration using reference images

batch processing

CSV/Excel export

validation statistics

measurement history

License

Choose and add an appropriate open-source or institutional license before publishing the repository.
