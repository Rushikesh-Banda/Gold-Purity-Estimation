# AI-Based Gold Purity Estimation

**Software Simulation for Non-Destructive Gold Assaying Using Artificial Intelligence (AI) and Machine Learning (ML) with Sample Datasets**

> **Disclaimer:** This application is an academic software simulation using sample/synthetic data. It is not a certified replacement for professional fire assay or XRF testing. The dataset is a *Synthetic/Simulated Sample Dataset for Academic Use*; none of its values are real laboratory measurements.

---

## 1. Project overview
A Python desktop application that estimates the purity (%) of a gold sample from eight numerical inputs (density, copper %, silver %, zinc %, nickel %, an XRF-like gold reading, temperature and weight). Three regression models are trained and compared, and the best one (chosen automatically from real test-set results) is saved and used by a Tkinter GUI.

## 2. Problem statement
Traditional gold testing such as fire assay damages the jewellery. Non-destructive methods such as XRF need expensive equipment. This project shows, in software only, how machine learning can estimate purity from measurement-like numbers without destroying a sample.

## 3. Objective
Build and evaluate a regression model on simulated data, compare three algorithms fairly, and deliver an easy-to-use GUI with validation, history and PDF reporting.

## 4. Features
- Synthetic dataset generator (1200 records, fixed seed)
- Data validation and cleaning (missing, duplicate, negative, unrealistic values)
- Linear Regression, Decision Tree and Random Forest with MAE, MSE, RMSE, R²
- Automatic best-model selection, saved with Joblib (preprocessing + model in one pipeline)
- Tkinter GUI: predict, clear, save, history, model performance, PDF report, "load sample from dataset"
- Input validation with clear error messages
- Matplotlib graphs, unit tests (45 tests)

## 5. Technologies used
Python, Pandas, NumPy, Scikit-learn, Tkinter, Matplotlib, Joblib, ReportLab (PDF). No deep learning, no hardware, no cloud.

## 6. Machine Learning approach
- **Type:** regression (purity is a continuous number).
- **Split:** 80% train / 20% test, `random_state=42`.
- **Pipeline:** `SimpleImputer(median)` -> `StandardScaler` -> model. Both are fitted on the training rows only, so there is **no data leakage**. The GUI loads the same fitted pipeline, so prediction uses exactly the same preprocessing.
- **Metrics:** MAE, MSE, RMSE and R². (R² is a goodness-of-fit score, *not* "accuracy".)
- **Selection rule:** lowest RMSE on the held-out test set (ties: higher R²). Five-fold cross-validation on the training data is also stored as a cross-check (`cv_rmse_mean`). The models use fixed simple settings and are not tuned, so the selection bias from using the test set is small; a more rigorous design would add a separate validation set.
- The model is trained once (`train_model.py`). Clicking *Predict* only loads the saved file.

### Actual results from the last training run
| Model | MAE | MSE | RMSE | R² |
|---|---|---|---|---|
| Linear Regression | 0.6954 | 0.9811 | 0.9905 | 0.9978 |
| Decision Tree Regressor | 1.2433 | 2.9979 | 1.7315 | 0.9933 |
| Random Forest Regressor | 0.9696 | 1.7807 | 1.3344 | 0.9960 |

**Selected model: Linear Regression** (lowest test RMSE). Random Forest did *not* win on this dataset: in the simulation density and the XRF-like reading depend almost linearly on purity, so a simple linear model fits it best. The very high R² reflects how strongly the *simulated* inputs relate to purity; it says nothing about real-world accuracy. Exact numbers are stored in `models/model_metrics.json` and are regenerated every time you train.

## 7. Dataset description
`data/gold_dataset.csv` - **Synthetic/Simulated Sample Dataset for Academic Use** (1200 rows).

| Column | Meaning |
|---|---|
| density | sample density (g/cm³) |
| copper_percent, silver_percent, zinc_percent, nickel_percent | alloy composition (%) |
| xrf_gold_reading | simulated XRF-like gold reading (%) |
| temperature | sample/environment temperature (°C) |
| weight | sample weight (g) |
| purity | reference/target gold purity (%) |

How it is simulated (see `src/dataset_generator.py`): purity is drawn around common grades (9K-24K) plus a uniform spread; the rest is split between alloy metals in yellow/rose/white "styles"; density follows the rule of mixtures with porosity, temperature and noise; the XRF-like reading is purity plus noise, a matrix effect and occasional surface-plating bias; measured percentages get their own noise. Weight and temperature are only weakly related to purity (they act as realistic "distractor" features).

## 8. Project architecture
```
CSV Dataset -> Data Validation -> Preprocessing -> Train/Test Split -> ML Models
   -> Model Evaluation -> Best Model Selection -> Saved Model (models/best_model.pkl)

Tkinter GUI -> User Input -> Input Validation -> Saved ML Model (same preprocessing)
   -> Predicted Purity -> Reference Purity Comparison -> Display -> Save History / PDF Report
```
```
Gold-Purity-Estimation/
|-- data/        gold_dataset.csv, test_samples.csv, prediction_history.csv
|-- models/      best_model.pkl, model_metrics.json, model_comparison.csv
|-- src/         config, dataset_generator, validation, preprocessing, train_model,
|                evaluation, visualization, predict, report_generator, main
|-- gui/         app.py
|-- outputs/     graphs/ (PNG), reports/ (PDF)
|-- tests/       unit tests
```

### UML entities -> code (for your diagrams)
| UML entity | Where in the code |
|---|---|
| User | the person using the GUI (actor, no class) |
| GUI | `gui/app.py` -> `GoldPurityApp` |
| Validator | `src/validation.py` -> `Validator` |
| GoldSample | `src/validation.py` -> `GoldSample` |
| DataPreprocessor | `src/preprocessing.py` -> `DataPreprocessor` (used in training) |
| MLModel | `src/predict.py` -> `MLModel` (loads `best_model.pkl`) |
| Prediction | `src/predict.py` -> `Prediction` |
| FireAssayReference | `src/predict.py` -> `FireAssayReference` (reference purity value only - **no fire assay is performed**) |
| Report | `src/report_generator.py` -> `Report` |
| Database/Dataset | `data/*.csv`, `PredictionHistory` class |

Relationships that really exist: `GoldPurityApp` -> `Validator` -> `GoldSample`; `GoldPurityApp` -> `MLModel` -> `Prediction`; `Prediction` has an optional `FireAssayReference`; `GoldPurityApp` -> `PredictionHistory` and `Report`. `DataPreprocessor` is used by the training script, **not** at prediction time by the user.

**Use cases.** *User:* enter sample data, validate input, predict purity, view result, compare with reference purity, view graphs, save/export result. *Admin/Developer:* manage dataset, train model, evaluate model, update model. Training is a separate developer activity - do **not** draw an `<<include>>` from the user's "Predict" use case to "Train model".

## 9. Installation
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
```
Tkinter ships with Python on Windows/macOS. On Ubuntu/Debian: `sudo apt install python3-tk`.

## 10. How to generate the dataset
```bash
python -m src.main generate
```
Prints the record count, number of features and min/max/mean purity.

## 11. How to train the model
```bash
python -m src.main train        # or:  python -m src.main all   (generate + train)
```
Writes the model, metrics, comparison table and four graphs in `outputs/graphs/`.

## 12. How to run the GUI
```bash
python -m src.main gui          # or:  python -m gui.app
```
Type the eight values (and optionally a reference purity) and click **Predict Purity**, or click **Load Sample from Dataset** to fill in a held-out sample that has a reference purity. If no reference purity is entered, the result shows "N/A". Example values from the brief: density 19.10, copper 3.50, silver 2.10, zinc 0.10, nickel 0.50, XRF-like reading 94.20, temperature 25, weight 10.

## 13. How to run the tests
```bash
python -m unittest discover -s tests -t . -v
```

## 14. Output screenshots
Add your own screenshots here after running the GUI:
- `[Screenshot: main window]`
- `[Screenshot: model performance window]`

Generated graphs: `outputs/graphs/model_comparison.png`, `actual_vs_predicted.png`, `residuals.png`, `purity_distribution.png`. Example PDF: `outputs/reports/sample_report.pdf`.

## AI Project Assistant
The GUI includes a small project-grounded **AI Project Assistant**. It answers common questions using the project's live dataset, saved model metrics, configuration and prediction history. It can explain the objective, dataset, eight features, workflow, algorithms, metrics, reports, limitations and GUI pages.

For prediction questions, the assistant can accept the eight measurement values and calls the same saved ML pipeline used by the Gold Sample Analysis page; it does not retrain the model. If a question is outside the project's available evidence, the assistant explicitly says it cannot answer accurately instead of inventing a project-specific fact.

## 15. Limitations
- Data are synthetic; results do not show how the method would perform on real jewellery.
- Relationships are simplified and partly linear, which favours Linear Regression.
- Models are not hyper-parameter tuned; one fixed split is used for the final comparison.
- No confidence interval is provided. The GUI only warns when an input lies outside the range seen in training.
- Predictions are clipped to 0-100 %.

## 16. Future enhancements
Real XRF data (with permission), hyper-parameter tuning with cross-validation, more alloy types, prediction intervals, exporting history to Excel.

## 17. Disclaimer
This application is an academic software simulation using sample/synthetic data. It is not a certified replacement for professional fire assay or XRF testing.

## Web application (localhost + deployment)

The project now includes a browser-based web frontend and Python API while keeping the original ML/model files and Tkinter application. The web UI uses the same saved `models/best_model.pkl` and the same validation/prediction code.

### Run locally
From the project root:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python backend/server.py
```

Open `http://127.0.0.1:8000`. The Python server serves the web frontend and API together, so prediction, dynamic sample charts, history, reports and the project-grounded AI assistant can be tested locally.

### Web architecture
- `frontend/` - browser UI (HTML/CSS/JavaScript)
- `backend/server.py` - zero-extra-framework Python API/server, suitable for Render
- Existing `src/` - validation, saved ML model, prediction, history, assistant and PDF reporting
- `render.yaml` - Render service configuration
- `vercel.json` - Vercel project configuration; deploy the `frontend` directory as the static frontend

### Render + Vercel
Deploy `backend/` + the project root to Render using `python backend/server.py`. Deploy the `frontend/` directory to Vercel. After the Render URL is available, set the frontend API base URL in `frontend/index.html` (before `app.js`) with:

```html
<script>window.GOLD_API_URL = "https://YOUR-RENDER-SERVICE.onrender.com";</script>
```

The frontend then sends predictions and assistant requests to the public Render API.

**Important:** `scikit-learn` is pinned to `1.9.1` because the saved model was trained with that version. Do not retrain the model merely for deployment.

## Web application
The project now includes a browser-based version in `frontend/` and a zero-dependency Python API in `backend/server.py`. Run `python run_web.py` and open `http://127.0.0.1:8000`. The web UI uses the saved ML pipeline for real predictions, compares all three saved model pipelines for the current sample, shows live sample analytics, loads all 1,200 dataset rows, lists/open PDFs, and includes the project-grounded AI assistant.
