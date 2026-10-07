"""
Project AI Assistant
--------------------
A small, deterministic, project-grounded assistant for the Gold Purity
Estimation application.

It deliberately uses the project's own README, configuration, metrics,
dataset/history and prediction pipeline as sources of truth. It does not
invent project-specific facts. Prediction requests are executed through the
same saved ML pipeline used by the GUI.
"""

import re
from pathlib import Path
from typing import Optional

import pandas as pd

from src import config
from src.evaluation import load_metrics
from src.predict import MLModel, PredictionHistory, run_prediction
from src.all_models import predict_all
from src.multilingual import SUPPORTED_LANGUAGES, normalize_user_text


class ProjectAssistant:
    """Answer common project questions from live project data."""

    def __init__(self, model=None):
        self.model = model
        self.history = PredictionHistory()
        self.project_root = config.PROJECT_ROOT

    def _metrics(self):
        try:
            return load_metrics()
        except Exception:
            return None

    def _dataset(self):
        try:
            if config.DATASET_PATH.exists():
                return pd.read_csv(config.DATASET_PATH)
        except Exception:
            pass
        return pd.DataFrame()

    def _readme(self):
        path = self.project_root / "README.md"
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def _model(self):
        if self.model is None:
            self.model = MLModel.load()
        return self.model

    @staticmethod
    def _contains(text, *terms):
        return any(term in text for term in terms)

    def _project_summary(self):
        metrics = self._metrics() or {}
        data = self._dataset()
        history = self.history.load()
        best = metrics.get("best_model", "not available")
        rmse = metrics.get("models", {}).get(best, {}).get("rmse")
        rows = len(data) if not data.empty else "not available"
        saved = len(history) if not history.empty else 0
        return (
            f"This project is an academic AI/ML software simulation for estimating "
            f"gold purity from eight measurement-like inputs. It uses a synthetic "
            f"dataset with {rows} rows, compares Linear Regression, Decision Tree "
            f"and Random Forest, and currently selects {best} as the best model "
            f"because it has the lowest test RMSE ({rmse:.4f}) when metrics are available. "
            f"The GUI supports prediction, validation, history, graphs and PDF reports. "
            f"There are currently {saved} saved prediction(s)."
        )

    def _model_answer(self):
        metrics = self._metrics()
        if not metrics:
            return "Model metrics are not available yet. Run `python -m src.main train` first."
        best = metrics.get("best_model", "—")
        criterion = metrics.get("selection_criterion", "lowest test RMSE")
        models = metrics.get("models", {})
        lines = [f"Selected model: {best}.", f"Selection rule: {criterion}."]
        for name, values in models.items():
            lines.append(
                f"{name}: MAE {values.get('mae', float('nan')):.4f}, "
                f"MSE {values.get('mse', float('nan')):.4f}, "
                f"RMSE {values.get('rmse', float('nan')):.4f}, "
                f"R² {values.get('r2', float('nan')):.4f}."
            )
        return "\n".join(lines)

    def _dataset_answer(self):
        data = self._dataset()
        if data.empty:
            return "The dataset file is not available right now."
        purity = data[config.TARGET_COLUMN]
        return (
            f"The synthetic academic dataset contains {len(data):,} rows and "
            f"{len(config.FEATURE_COLUMNS)} input features. Purity ranges from "
            f"{purity.min():.2f}% to {purity.max():.2f}%, with a mean of "
            f"{purity.mean():.2f}%. The eight inputs are density, copper %, silver %, "
            f"zinc %, nickel %, XRF-like gold reading, temperature and weight."
        )

    def _history_answer(self):
        history = self.history.load()
        if history.empty:
            return "There are no saved predictions yet. Make a prediction and use Save Result."
        last = history.iloc[-1]
        return (
            f"There are {len(history)} saved prediction(s). The latest saved prediction "
            f"was {last.get('Predicted Purity', '—')}% using {last.get('Model Used', '—')} "
            f"at {last.get('Date/Time', '—')}."
        )

    def _metrics_definition(self):
        return (
            "MAE is the mean absolute error; MSE is mean squared error; RMSE is the "
            "square root of MSE and is used for model selection here; R² is a goodness-of-fit "
            "score. R² is not the same thing as real-world prediction accuracy."
        )

    def _workflow_answer(self):
        return (
            "The project workflow is: synthetic CSV dataset → validation/cleaning → "
            "80/20 train-test split → preprocessing with median imputation and standard "
            "scaling → three regression models → evaluation with MAE/MSE/RMSE/R² → "
            "lowest-test-RMSE model selected and saved → GUI loads the saved pipeline → "
            "prediction → optional reference comparison → history/PDF report."
        )

    def _technology_answer(self):
        return (
            "Technologies used are Python, Pandas, NumPy, Scikit-learn, Tkinter, "
            "Matplotlib, Joblib and ReportLab. The project uses no deep learning, "
            "hardware or cloud service for the core application."
        )

    def _generation_answer(self):
        return (
            "The dataset is synthetic/simulated for academic use. The generator creates measurement-like "
            "features and a continuous purity target with controlled relationships and noise, then writes "
            "the data to data/gold_dataset.csv. The current dataset contains 1,200 rows. It is not laboratory data."
        )

    def _preprocessing_answer(self):
        return (
            "Before training, the project loads and cleans the CSV, checks the required columns and numeric values, "
            "removes duplicate/bad rows where applicable, then uses an 80/20 train-test split. The training pipeline "
            "uses median imputation followed by standard scaling, fitted on the training data only, before the regression model."
        )

    def _report_answer(self):
        return (
            "The Reports page uses the existing ReportLab report generator. After a successful prediction, Generate PDF "
            "creates a PDF containing the sample inputs, predicted purity, optional reference comparison and model metrics. "
            "Existing PDFs are listed on the Reports page and can be opened from there."
        )

    def _graphs_answer(self):
        return (
            "Visual Analytics shows four existing evaluation graphs: Model Comparison, Actual vs Predicted, Prediction Errors "
            "(residuals), and Purity Distribution. They are generated from the project's evaluation/visualization pipeline and "
            "use the saved model metrics and test predictions."
        )

    def _files_answer(self):
        return (
            "The main project folders are data (CSV datasets/history), models (saved pipeline and metrics), src (ML, validation, "
            "prediction, reporting and visualization logic), gui (Tkinter application), outputs (graphs and PDFs), and tests (automated tests)."
        )

    def _prediction_flow_answer(self):
        return (
            "When you click Predict Purity, the GUI sends the eight entered values to the existing validation layer. Valid values "
            "are converted into the project's GoldSample, passed through the saved preprocessing/model pipeline, and the result is "
            "clipped to the 0–100% purity range. If a reference purity was entered, the absolute difference is also calculated. "
            "The model is loaded; it is not retrained during prediction."
        )

    def _algorithm_answer(self, algorithm):
        if algorithm == "linear":
            return (
                "Linear Regression models purity as a continuous target using a linear combination "
                "of the eight input features. In this project it was selected because it achieved "
                "the lowest held-out test RMSE. The README also notes that density and the simulated "
                "XRF-like reading depend almost linearly on purity in the synthetic data."
            )
        if algorithm == "tree":
            return (
                "Decision Tree Regressor is one of the three evaluated regression models. It learns "
                "non-linear decision rules by splitting the feature space into regions and predicting "
                "a continuous purity value in each region. Its test RMSE in the current metrics is "
                f"{self._metrics().get('models', {}).get('Decision Tree Regressor', {}).get('rmse', float('nan')):.4f}."
            )
        return (
            "Random Forest Regressor is one of the three evaluated models. It combines many decision "
            "trees to produce a regression estimate. In this dataset it did not win model selection; "
            f"its current test RMSE is {self._metrics().get('models', {}).get('Random Forest Regressor', {}).get('rmse', float('nan')):.4f}."
        )

    def _feature_answer(self, question):
        q = question.lower()
        details = {
            "density": "Density is the sample density in g/cm³.",
            "copper": "Copper % is the copper fraction of the alloy composition.",
            "silver": "Silver % is the silver fraction of the alloy composition.",
            "zinc": "Zinc % is the zinc fraction of the alloy composition.",
            "nickel": "Nickel % is the nickel fraction of the alloy composition.",
            "xrf": "XRF-like Gold Reading is a simulated XRF-like gold percentage; this project does not perform real XRF testing.",
            "temperature": "Temperature is the sample/environment temperature in °C and acts as a weakly related feature in the simulation.",
            "weight": "Weight is the sample weight in grams and acts as a weakly related distractor feature in the simulation.",
        }
        for key, answer in details.items():
            if key in q:
                return answer
        return self._dataset_answer()

    def _fire_assay_answer(self):
        return (
            "Fire assay is mentioned as a traditional destructive gold-testing method in the project "
            "problem statement. This software does not perform a fire assay; its reference-purity field "
            "is only a reference value used to compare with the ML prediction."
        )

    def _limitations_answer(self):
        return (
            "The data are synthetic, relationships are simplified and partly linear, "
            "the models are not hyper-parameter tuned, the final comparison uses one "
            "fixed train/test split, and the GUI does not provide a confidence interval. "
            "Predictions are clipped to 0–100%. This is not a certified replacement for "
            "professional fire assay or XRF testing."
        )

    def _parse_prediction_inputs(self, question):
        """Parse labelled inputs or eight numeric values in feature order."""
        q = question.lower().replace("°", "")
        aliases = {
            "density": ["density"],
            "copper_percent": ["copper", "cu"],
            "silver_percent": ["silver", "ag"],
            "zinc_percent": ["zinc", "zn"],
            "nickel_percent": ["nickel", "ni"],
            "xrf_gold_reading": ["xrf", "gold reading", "xrf reading"],
            "temperature": ["temperature", "temp"],
            "weight": ["weight"],
        }
        found = {}
        for name, names in aliases.items():
            for alias in names:
                # value can appear after ':', '=', or as "alias 19.2"
                pattern = rf"(?:{re.escape(alias)})\s*(?:is|=|:)?\s*(-?\d+(?:\.\d+)?)"
                match = re.search(pattern, q)
                if match:
                    found[name] = match.group(1)
                    break

        if len(found) == len(config.FEATURE_COLUMNS):
            return found, None

        # For a prediction request containing exactly eight/fewer useful numbers,
        # accept them in the documented feature order only when there are exactly 8.
        numbers = re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", q)
        if len(numbers) == 8:
            return dict(zip(config.FEATURE_COLUMNS, numbers)), None
        if found:
            missing = [config.FIELD_RULES[n].label for n in config.FEATURE_COLUMNS if n not in found]
            return None, "I found some measurements, but I still need: " + ", ".join(missing) + "."
        return None, None

    def _prediction_answer(self, question):
        inputs, error = self._parse_prediction_inputs(question)
        if error:
            return error
        if inputs is None:
            return (
                "I can run the real saved ML model. Give all eight values using labels, "
                "for example: density 19.039, copper 0.158, silver 0, zinc 0, "
                "nickel 0.156, xrf 100, temperature 23.3, weight 10.71."
            )
        try:
            reference_match = re.search(
                r"(?:reference|ref(?:erence)? purity)\s*(?:is|=|:)?\s*(\d+(?:\.\d+)?)",
                question.lower(),
            )
            reference = reference_match.group(1) if reference_match else None
            prediction = run_prediction(inputs, reference, model=self._model())
        except Exception as exc:
            return f"I could not run the saved model: {exc}"

        try:
            all_predictions = predict_all(inputs)
            comparison = " ".join(f"{name}: {value:.2f}%" for name, value in all_predictions.items())
            answer = (
                f"Real model predictions for this sample — {comparison}. "
                f"Selected model: {prediction.model_name} at {prediction.predicted_purity:.2f}%."
            )
        except Exception:
            answer = (
                f"Real model prediction: {prediction.predicted_purity:.2f}% purity using "
                f"{prediction.model_name}."
            )
        if prediction.reference_purity is not None:
            answer += f" Reference purity: {prediction.reference_purity:.2f}%. Absolute difference: {prediction.difference:.2f}%."
        if prediction.warnings:
            answer += "\nWarning: " + " ".join(prediction.warnings)
        return answer

    @staticmethod
    def _normalize_multilingual(text):
        return normalize_user_text(text)

    @staticmethod
    def _translate_answer(answer, language):
        if language == 'en': return answer
        # Translate stable project phrases while preserving live numbers/model names.
        if language == 'te':
            pairs=[
                ("Hello! I am the Gold Purity Project Assistant.","నమస్కారం! నేను గోల్డ్ ప్యూరిటీ ప్రాజెక్ట్ సహాయకుడిని."),
                ("The synthetic academic dataset contains","సింథటిక్ అకాడమిక్ డేటాసెట్‌లో"),("rows and","వరుసలు మరియు"),("input features.","ఇన్‌పుట్ ఫీచర్లు ఉన్నాయి."),
                ("Purity ranges from","స్వచ్ఛత పరిధి"),("with a mean of","మరియు సగటు"),("The eight inputs are","ఎనిమిది ఇన్‌పుట్లు:"),
                ("Selected model:","ఎంచుకున్న మోడల్:"),("Selection rule:","ఎంపిక నియమం:"),("Model metrics are not available yet.","మోడల్ మెట్రిక్స్ ఇంకా అందుబాటులో లేవు."),
                ("MAE","MAE"),("MSE","MSE"),("RMSE","RMSE"),("R²","R²"),("The project workflow is:","ప్రాజెక్ట్ వర్క్‌ఫ్లో:"),
                ("The project is an academic AI/ML software simulation","ఇది అకాడమిక్ AI/ML సాఫ్ట్‌వేర్ సిమ్యులేషన్."),
                ("The data are synthetic","డేటా సింథటిక్"),("This is not a certified replacement for professional fire assay or XRF testing.","ఇది ప్రొఫెషనల్ ఫైర్ అసే లేదా XRF పరీక్షకు సర్టిఫైడ్ ప్రత్యామ్నాయం కాదు."),
                ("Real model predictions for this sample —","ఈ నమూనాకు నిజమైన మోడల్ అంచనాలు —"),("Linear Regression","లీనియర్ రిగ్రెషన్"),("Decision Tree Regressor","డెసిషన్ ట్రీ రిగ్రెసర్"),("Random Forest Regressor","రాండమ్ ఫారెస్ట్ రిగ్రెసర్"),("Selected model:","ఎంచుకున్న మోడల్:"),("Reference purity:","రిఫరెన్స్ స్వచ్ఛత:"),("Absolute difference:","సంపూర్ణ తేడా:"),
                ("I could not run the saved model:","సేవ్ చేసిన మోడల్‌ను అమలు చేయలేకపోయాను:"),("Gold purity is the percentage of gold in the sample.","బంగారం స్వచ్ఛత అంటే నమూనాలో ఉన్న బంగారం శాతం."),("In this project it is the continuous target estimated by the saved ML models from eight input measurements.","ఈ ప్రాజెక్ట్‌లో ఎనిమిది ఇన్‌పుట్ కొలతల ఆధారంగా సేవ్ చేసిన ML మోడళ్లు అంచనా వేసే టార్గెట్ ఇదే."),("I can run the real saved ML model.","నేను సేవ్ చేసిన నిజమైన ML మోడల్‌ను అమలు చేయగలను."),
                ("There are no saved predictions yet.","ఇంకా సేవ్ చేసిన అంచనాలు లేవు."),("There are","ఉన్నాయి"),("saved prediction(s).","సేవ్ చేసిన అంచనాలు."),
                ("The latest saved prediction was","తాజా సేవ్ చేసిన అంచనా"),("using","ఉపయోగించి"),("at","సమయంలో"),("The dataset file is not available right now.","డేటాసెట్ ఫైల్ ప్రస్తుతం అందుబాటులో లేదు."),
                ("Density is the sample density in g/cm³.","సాంద్రత నమూనా సాంద్రత, g/cm³ లో."),("Copper % is the copper fraction of the alloy composition.","Copper % మిశ్రమంలోని రాగి శాతం."),
                ("Silver % is the silver fraction of the alloy composition.","Silver % మిశ్రమంలోని వెండి శాతం."),("Zinc % is the zinc fraction of the alloy composition.","Zinc % మిశ్రమంలోని జింక్ శాతం."),
                ("Nickel % is the nickel fraction of the alloy composition.","Nickel % మిశ్రమంలోని నికెల్ శాతం."),("Temperature is the sample/environment temperature in °C","ఉష్ణోగ్రత నమూనా/పరిసర ఉష్ణోగ్రత, °C లో"),("Weight is the sample weight in grams","బరువు నమూనా బరువు, గ్రాముల్లో"),
                ("XRF-like Gold Reading is a simulated XRF-like gold percentage; this project does not perform real XRF testing.","XRF తరహా Gold Reading సిమ్యులేటెడ్ XRF బంగారం శాతం; ఈ ప్రాజెక్ట్ నిజమైన XRF పరీక్ష చేయదు."),
                ("I don't have enough project-grounded information to answer that accurately, so I won't guess.","ఖచ్చితంగా సమాధానం ఇవ్వడానికి తగిన ప్రాజెక్ట్ సమాచారం లేదు, కాబట్టి నేను ఊహించను."),
            ]
        else:
            pairs=[
                ("Hello! I am the Gold Purity Project Assistant.","नमस्ते! मैं गोल्ड प्योरिटी प्रोजेक्ट सहायक हूँ."),
                ("The synthetic academic dataset contains","सिंथेटिक अकादमिक डेटासेट में"),("rows and","पंक्तियाँ और"),("input features.","इनपुट फीचर हैं."),
                ("Purity ranges from","शुद्धता की सीमा"),("with a mean of","और औसत"),("The eight inputs are","आठ इनपुट हैं:"),
                ("Selected model:","चयनित मॉडल:"),("Selection rule:","चयन नियम:"),("Model metrics are not available yet.","मॉडल मेट्रिक्स अभी उपलब्ध नहीं हैं."),
                ("The project workflow is:","प्रोजेक्ट वर्कफ़्लो:"),("The project is an academic AI/ML software simulation","यह एक अकादमिक AI/ML सॉफ्टवेयर सिमुलेशन है."),
                ("The data are synthetic","डेटा सिंथेटिक है"),("This is not a certified replacement for professional fire assay or XRF testing.","यह पेशेवर फायर अस्से या XRF परीक्षण का प्रमाणित विकल्प नहीं है."),
                ("Real model predictions for this sample —","इस नमूने के वास्तविक मॉडल अनुमान —"),("Linear Regression","लीनियर रिग्रेशन"),("Decision Tree Regressor","डिसीजन ट्री रिग्रेसर"),("Random Forest Regressor","रैंडम फॉरेस्ट रिग्रेसर"),("Reference purity:","संदर्भ शुद्धता:"),("Absolute difference:","पूर्ण अंतर:"),
                ("I could not run the saved model:","सेव किए गए मॉडल को चला नहीं सका:"),("Gold purity is the percentage of gold in the sample.","सोने की शुद्धता नमूने में सोने का प्रतिशत है."),("In this project it is the continuous target estimated by the saved ML models from eight input measurements.","इस प्रोजेक्ट में यह आठ इनपुट मापों के आधार पर सेव किए गए ML मॉडलों द्वारा अनुमानित टारगेट है."),("I can run the real saved ML model.","मैं सेव किए गए वास्तविक ML मॉडल को चला सकता हूँ."),
                ("There are no saved predictions yet.","अभी कोई सेव किया हुआ अनुमान नहीं है."),("There are","कुल"),("saved prediction(s).","सेव किए गए अनुमान हैं."),
                ("The latest saved prediction was","नवीनतम सेव किया गया अनुमान था"),("using","का उपयोग करके"),("at","समय"),("The dataset file is not available right now.","डेटासेट फ़ाइल अभी उपलब्ध नहीं है."),
                ("Density is the sample density in g/cm³.","घनत्व नमूने का घनत्व है, g/cm³ में."),("Copper % is the copper fraction of the alloy composition.","Copper % मिश्रधातु में तांबे का प्रतिशत है."),
                ("Silver % is the silver fraction of the alloy composition.","Silver % मिश्रधातु में चाँदी का प्रतिशत है."),("Zinc % is the zinc fraction of the alloy composition.","Zinc % मिश्रधातु में जस्ता का प्रतिशत है."),
                ("Nickel % is the nickel fraction of the alloy composition.","Nickel % मिश्रधातु में निकेल का प्रतिशत है."),("Temperature is the sample/environment temperature in °C","तापमान नमूने/पर्यावरण का तापमान है, °C में"),("Weight is the sample weight in grams","वजन नमूने का वजन है, ग्राम में"),
                ("XRF-like Gold Reading is a simulated XRF-like gold percentage; this project does not perform real XRF testing.","XRF जैसा Gold Reading एक सिमुलेटेड XRF सोने का प्रतिशत है; यह प्रोजेक्ट वास्तविक XRF परीक्षण नहीं करता."),
                ("I don't have enough project-grounded information to answer that accurately, so I won't guess.","सटीक उत्तर देने के लिए पर्याप्त प्रोजेक्ट जानकारी नहीं है, इसलिए मैं अनुमान नहीं लगाऊँगा."),
            ]
        out=answer
        for a,b in pairs: out=out.replace(a,b)
        return out

    def _answer_en(self, question: str) -> str:
        """Return a grounded English answer from project data."""
        q = (question or "").strip()
        if not q:
            return "Ask me about the project, dataset, models, metrics, workflow, predictions, history, reports or limitations."
        q_for_logic = self._normalize_multilingual(q)
        text = re.sub(r"\s+", " ", q_for_logic.lower())
        q = q_for_logic

        # If the user supplies all eight labelled measurements, treat it as a real
        # prediction request even when they do not explicitly say "predict".
        parsed_inputs, parsed_error = self._parse_prediction_inputs(q)
        if parsed_inputs is not None:
            return self._prediction_answer(q)
        if any(word in text for word in ["predict", "prediction", "estimate", "calculate purity"]):
            if parsed_error or any(k in text for k in ["density", "copper", "silver", "zinc", "nickel", "xrf", "temperature", "weight"]):
                return self._prediction_answer(q)

        if self._contains(text, "what is this project", "about this project", "project objective", "purpose", "what does this project do", "what is the objective", "what happened in this project", "what is happening in the project", "project status"):
            return self._project_summary()
        if self._contains(text, "how does it work", "how does the project work", "how the project works", "how does prediction work", "prediction flow", "workflow", "flow of the project", "architecture", "click predict", "when i click predict", "what happens when i predict"):
            return self._prediction_flow_answer() if self._contains(text, "predict") else self._workflow_answer()
        if self._contains(text, "generate dataset", "generated dataset", "dataset generated", "how was the dataset", "where does the dataset come from", "synthetic data"):
            return self._generation_answer()
        if self._contains(text, "preprocess", "preprocessing", "cleaning", "scaling", "imputation", "train test split"):
            return self._preprocessing_answer()
        if self._contains(text, "linear regression"):
            return self._algorithm_answer("linear")
        if self._contains(text, "decision tree"):
            return self._algorithm_answer("tree")
        if self._contains(text, "random forest"):
            return self._algorithm_answer("forest")
        if self._contains(text, "fire assay", "destructive testing"):
            return self._fire_assay_answer()
        if self._contains(text, "gold", "purity") and self._contains(text, "what is", "how much", "meaning"):
            return "Gold purity is the percentage of gold in the sample. In this project it is the continuous target estimated by the saved ML models from eight input measurements."
        if self._contains(text, "dataset", "how many samples", "how many rows", "features", "inputs"):
            return self._dataset_answer()
        if self._contains(text, "xrf", "density", "copper", "silver", "zinc", "nickel", "temperature", "weight") and self._contains(text, "what is", "meaning", "mean", "feature"):
            return self._feature_answer(text)
        if self._contains(text, "three models", "3 models", "all three models", "best model", "selected model", "which model", "model performance", "compare models", "compare the models"):
            return self._model_answer()
        if self._contains(text, "mae", "mse", "rmse", "r2", "r²", "metrics", "metric"):
            return self._metrics_definition()
        if self._contains(text, "technology", "technologies", "tech stack", "libraries", "tools used"):
            return self._technology_answer()
        if self._contains(text, "history", "saved prediction", "latest prediction"):
            return self._history_answer()
        if self._contains(text, "report", "pdf"):
            return self._report_answer()
        if self._contains(text, "page", "pages", "screen", "dashboard", "analytics", "dataset explorer", "model & system", "about"):
            return "The GUI contains Dashboard, Gold Sample Analysis, Visual Analytics, Prediction History, Dataset Explorer, Reports, Model & System, AI Project Assistant and About. Each page is connected to the project's existing data or ML/reporting functionality."
        if self._contains(text, "limitation", "limitations", "real gold", "real world", "accurate in real life"):
            return self._limitations_answer()
        if self._contains(text, "validate", "validation", "invalid input", "allowed range"):
            return "The project validates all eight inputs against the ranges defined in src/config.py and reports invalid or unrealistic values before prediction. Inputs outside the training range can also produce a reliability warning."
        if self._contains(text, "train", "training", "retrain"):
            return "Training is a separate developer activity. Use `python -m src.main train` to train and compare the three models. Clicking Predict does not retrain; it loads the saved pipeline."
        if self._contains(text, "graph", "graphs", "visual analytics", "charts"):
            return self._graphs_answer()
        if self._contains(text, "file structure", "folders", "files", "project folders", "where is"):
            return self._files_answer()
        if self._contains(text, "hello", "hi", "hey"):
            return "Hello! I am the Gold Purity Project Assistant. Ask me anything about this project's dataset, ML models, metrics, workflow, reports, history or predictions."

        return (
            "I don't have enough project-grounded information to answer that accurately, "
            "so I won't guess. Try asking about the objective, dataset, eight inputs, "
            "models, RMSE/R², workflow, graphs, history, reports, limitations, or give "
            "eight measurements for a real model prediction."
        )

    def answer(self, question: str, language: str = "en") -> str:
        language = language if language in SUPPORTED_LANGUAGES else "en"
        answer = self._answer_en(question)
        return self._translate_answer(answer, language)
