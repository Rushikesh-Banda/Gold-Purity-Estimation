"""
report_generator.py
-------------------
Creates a PDF report of one prediction with ReportLab.
"""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from src import config
from src.evaluation import load_metrics


class Report:
    """Builds and saves the PDF report for one Prediction."""

    def __init__(self, prediction, metrics=None):
        self.prediction = prediction
        self.metrics = metrics            # dict from model_metrics.json (optional)

    @staticmethod
    def _table(data, col_widths, header=True):
        table = Table(data, colWidths=col_widths)
        style = [("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                 ("FONTSIZE", (0, 0), (-1, -1), 9),
                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
        if header:
            style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c9a227")),
                      ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
        table.setStyle(TableStyle(style))
        return table

    def save(self, output_dir=None):
        """Write the PDF and return its path."""
        output_dir = output_dir or config.REPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"gold_purity_report_{datetime.now():%Y%m%d_%H%M%S}.pdf"

        styles = getSampleStyleSheet()
        small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8.5, leading=11)
        p = self.prediction
        s = p.sample
        ref = "Not available" if p.reference_purity is None else f"{p.reference_purity:.2f} %"
        diff = "Not available" if p.difference is None else f"{p.difference:.2f} %"

        story = [
            Paragraph(config.APP_TITLE, styles["Title"]),
            Paragraph(config.APP_SUBTITLE, styles["Heading3"]),
            Paragraph(f"Report date/time: {p.timestamp:%Y-%m-%d %H:%M:%S}", styles["Normal"]),
            Spacer(1, 0.4 * cm),
            Paragraph("Input sample values", styles["Heading2"]),
        ]
        inputs = [["Parameter", "Value"]]
        for name in config.FEATURE_COLUMNS:
            rule = config.FIELD_RULES[name]
            inputs.append([rule.label, f"{getattr(s, name):g} {rule.unit}".strip()])
        story += [self._table(inputs, [8 * cm, 6 * cm]), Spacer(1, 0.4 * cm),
                  Paragraph("Result", styles["Heading2"]),
                  self._table([["Predicted purity", f"{p.predicted_purity:.2f} %"],
                               ["Reference purity", ref],
                               ["Absolute difference", diff],
                               ["Selected ML model", p.model_name]],
                              [8 * cm, 6 * cm], header=False)]
        for note in p.warnings:
            story.append(Paragraph(f"Warning: {note}", small))

        if self.metrics:
            story += [Spacer(1, 0.4 * cm), Paragraph("Model evaluation (test set)", styles["Heading2"])]
            rows = [["Model", "MAE", "MSE", "RMSE", "R2"]]
            for name, m in self.metrics["models"].items():
                rows.append([name, f"{m['mae']:.4f}", f"{m['mse']:.4f}", f"{m['rmse']:.4f}", f"{m['r2']:.4f}"])
            story += [self._table(rows, [5.5 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm, 2.4 * cm]),
                      Paragraph(f"Selection rule: {self.metrics['selection_criterion']}. "
                                f"Dataset: {self.metrics['dataset']}.", small)]

        story += [Spacer(1, 0.6 * cm), Paragraph("Disclaimer", styles["Heading2"]),
                  Paragraph(config.DISCLAIMER, styles["Normal"])]
        SimpleDocTemplate(str(path), pagesize=A4, title="Gold Purity Report",
                          leftMargin=2 * cm, rightMargin=2 * cm).build(story)
        return path


def generate_pdf_report(prediction, metrics=None, output_dir=None):
    """Create a PDF report; loads the saved metrics automatically if none are given."""
    if metrics is None:
        try:
            metrics = load_metrics()
        except FileNotFoundError:
            metrics = None            # report is still created, without the metrics table
    return Report(prediction, metrics).save(output_dir)
