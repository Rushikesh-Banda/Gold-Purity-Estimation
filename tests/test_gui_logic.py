"""
GUI logic test WITHOUT a display.

Real Tkinter windows cannot be opened in automated tests (and Tkinter may not
even be installed), so the tkinter modules are replaced by mocks. This checks
that the button handlers call the validator/model/history correctly and show
the right messages. It does NOT check how the window looks.
"""

import importlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.predict import MLModel, ModelNotFoundError, PredictionHistory
from tests.helpers import VALID_INPUT, build_test_artifacts


class FakeStringVar:
    def __init__(self, value=""):
        self._value = value

    def get(self):
        return self._value

    def set(self, value):
        self._value = value


class TestGuiHandlers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.tmp.name)
        cls.paths = build_test_artifacts(cls.folder)
        cls.model = MLModel.load(cls.paths["model"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        fake_tk = mock.MagicMock()
        fake_tk.StringVar = FakeStringVar
        self.messagebox = mock.MagicMock()
        fake_tk.messagebox = self.messagebox
        fake_tk.ttk = mock.MagicMock()
        modules = {"tkinter": fake_tk, "tkinter.ttk": fake_tk.ttk, "tkinter.messagebox": self.messagebox}
        with mock.patch.dict(sys.modules, modules):
            sys.modules.pop("gui.app", None)
            app_module = importlib.import_module("gui.app")
        sys.modules.pop("gui.app", None)
        self.app = app_module.GoldPurityApp(mock.MagicMock(), model=self.model)
        self.app.history = PredictionHistory(self.folder / "gui_history.csv")

    def fill(self, **changes):
        for name, value in dict(VALID_INPUT, **changes).items():
            self.app.input_vars[name].set(value)

    def test_valid_prediction_updates_result_labels(self):
        self.fill()
        self.app.reference_input_var.set("95")
        self.app.on_predict()
        self.messagebox.showerror.assert_not_called()
        self.assertRegex(self.app.predicted_var.get(), r"Predicted Gold Purity: \d+\.\d\d %")
        self.assertRegex(self.app.difference_var.get(), r"Difference: \d+\.\d\d %")
        self.assertIn(self.model.model_name, self.app.model_var.get())

    def test_invalid_input_shows_error_and_no_result(self):
        self.fill(density="abc")
        self.app.on_predict()
        self.messagebox.showerror.assert_called_once()
        self.assertIn("valid numeric value", self.messagebox.showerror.call_args[0][1])
        self.assertIsNone(self.app.last_prediction)

    def test_empty_form_shows_error(self):
        self.app.on_predict()
        self.messagebox.showerror.assert_called_once()

    def test_save_requires_prediction_then_writes_history(self):
        self.app.on_save()
        self.messagebox.showwarning.assert_called_once()
        self.fill()
        self.app.on_predict()
        self.app.on_save()
        self.assertEqual(len(self.app.history.load()), 1)

    def test_clear_resets_everything(self):
        self.fill()
        self.app.on_predict()
        self.app.on_clear()
        self.assertEqual(self.app.input_vars["density"].get(), "")
        self.assertIsNone(self.app.last_prediction)
        self.assertEqual(self.app.predicted_var.get(), "Predicted Gold Purity: -")

    def test_history_with_no_file_shows_info_message(self):
        self.app.on_view_history()
        self.messagebox.showinfo.assert_called_once()

    def test_missing_model_shows_error(self):
        self.app._model = None
        with mock.patch.object(MLModel, "load", side_effect=ModelNotFoundError("no model")):
            self.fill()
            self.app.on_predict()
        self.messagebox.showerror.assert_called_once()


if __name__ == "__main__":
    unittest.main()
