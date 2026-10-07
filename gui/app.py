"""
gui/app.py
----------
Professional multi-page Tkinter desktop application for the AI-Based Gold
Purity Estimation academic simulation.

The GUI is intentionally a presentation layer.  Existing ML/prediction,
validation, history, reporting and visualization modules remain the source of
truth; this file only connects them to a richer desktop interface.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import pandas as pd
from PIL import Image, ImageTk

from src import config
from src.evaluation import load_metrics
from src.project_assistant import ProjectAssistant
from src.predict import (
    MLModel,
    ModelNotFoundError,
    PredictionHistory,
    get_random_test_sample,
    run_prediction,
)
from src.report_generator import generate_pdf_report
from src.validation import InputValidationError
from src.visualization import GRAPH_FILES


class GoldPurityApp:
    """Main multi-page application window."""

    NAV_ITEMS = [
        ("Dashboard", "dashboard"),
        ("Gold Sample Analysis", "analysis"),
        ("Visual Analytics", "analytics"),
        ("Prediction History", "history"),
        ("Dataset Explorer", "dataset"),
        ("Reports", "reports"),
        ("Model & System", "system"),
        ("AI Assistant", "assistant"),
        ("About", "about"),
    ]

    def __init__(self, root, model=None):
        self.root = root
        self._model = model
        self.last_prediction = None
        self.history = PredictionHistory()
        self._images = []
        self._pages = {}
        self._nav_buttons = {}
        self.assistant = ProjectAssistant(model=model)

        self.input_vars = {name: tk.StringVar() for name in config.FEATURE_COLUMNS}
        self.reference_input_var = tk.StringVar()

        # Full strings are retained for backward-compatible tests/logging.
        # The UI uses the concise display variables below to prevent clipping.
        self.predicted_var = tk.StringVar(value="Predicted Gold Purity: -")
        self.reference_var = tk.StringVar(value="Reference Purity: -")
        self.difference_var = tk.StringVar(value="Difference: -")
        self.model_var = tk.StringVar(value="Selected Model: -")
        self.predicted_display_var = tk.StringVar(value="-")
        self.reference_display_var = tk.StringVar(value="-")
        self.difference_display_var = tk.StringVar(value="-")
        self.model_display_var = tk.StringVar(value="-")
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self.show_page("dashboard")

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.root.title(config.APP_TITLE)
        self.root.geometry("1240x820")
        self.root.minsize(1050, 700)
        try:
            self.root.configure(bg="#f5f7fb")
        except Exception:
            pass

        self._configure_styles()

        shell = ttk.Frame(self.root, style="App.TFrame")
        shell.pack(fill="both", expand=True)

        self.sidebar = ttk.Frame(shell, style="Sidebar.TFrame", width=235)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_area = ttk.Frame(shell, style="Main.TFrame")
        self.main_area.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._build_main_area()
        self._build_status_bar()
        self._create_floating_assistant()
        self.root.after(250, self._show_floating_assistant)

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        styles = {
            "App.TFrame": {"background": "#f5f7fb"},
            "Main.TFrame": {"background": "#f5f7fb"},
            "Sidebar.TFrame": {"background": "#172033"},
            "SidebarTitle.TLabel": {
                "background": "#172033", "foreground": "#f8fafc",
                "font": ("Segoe UI", 16, "bold")
            },
            "SidebarSub.TLabel": {
                "background": "#172033", "foreground": "#aeb9cc",
                "font": ("Segoe UI", 9)
            },
            "Nav.TButton": {
                "background": "#172033", "foreground": "#d8e0ee",
                "font": ("Segoe UI", 10, "bold"), "padding": (12, 10),
                "anchor": "w", "borderwidth": 0
            },
            "NavActive.TButton": {
                "background": "#c9a227", "foreground": "#172033",
                "font": ("Segoe UI", 10, "bold"), "padding": (12, 10),
                "anchor": "w", "borderwidth": 0
            },
            "PageTitle.TLabel": {
                "background": "#f5f7fb", "foreground": "#172033",
                "font": ("Segoe UI", 23, "bold")
            },
            "PageSubtitle.TLabel": {
                "background": "#f5f7fb", "foreground": "#64748b",
                "font": ("Segoe UI", 10)
            },
            "Card.TFrame": {"background": "#ffffff"},
            "CardTitle.TLabel": {
                "background": "#ffffff", "foreground": "#64748b",
                "font": ("Segoe UI", 9, "bold")
            },
            "CardValue.TLabel": {
                "background": "#ffffff", "foreground": "#172033",
                "font": ("Segoe UI", 19, "bold")
            },
            "Section.TLabel": {
                "background": "#f5f7fb", "foreground": "#172033",
                "font": ("Segoe UI", 13, "bold")
            },
            "Body.TLabel": {
                "background": "#ffffff", "foreground": "#334155",
                "font": ("Segoe UI", 10)
            },
            "Muted.TLabel": {
                "background": "#ffffff", "foreground": "#64748b",
                "font": ("Segoe UI", 9)
            },
            "Gold.TButton": {
                "background": "#c9a227", "foreground": "#172033",
                "font": ("Segoe UI", 10, "bold"), "padding": (12, 8)
            },
            "Secondary.TButton": {
                "background": "#e8edf5", "foreground": "#172033",
                "font": ("Segoe UI", 10, "bold"), "padding": (10, 7)
            },
            "Danger.TButton": {
                "background": "#fee2e2", "foreground": "#991b1b",
                "font": ("Segoe UI", 10, "bold"), "padding": (10, 7)
            },
            "Status.TLabel": {
                "background": "#e8edf5", "foreground": "#475569",
                "font": ("Segoe UI", 9), "padding": (8, 5)
            },
            "Disclaimer.TLabel": {
                "background": "#fff7e0", "foreground": "#73520a",
                "font": ("Segoe UI", 9), "padding": (10, 8)
            },
        }
        for name, options in styles.items():
            try:
                style.configure(name, **options)
            except Exception:
                pass

        try:
            style.configure(
                "Treeview", background="#ffffff", fieldbackground="#ffffff",
                foreground="#243044", rowheight=30, font=("Segoe UI", 9)
            )
            style.configure(
                "Treeview.Heading", background="#e8edf5", foreground="#172033",
                font=("Segoe UI", 9, "bold"), padding=7
            )
            style.map("Treeview", background=[("selected", "#dce8f7")])
        except Exception:
            pass

    def _build_sidebar(self):
        header = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        header.pack(fill="x", padx=18, pady=(25, 22))
        ttk.Label(header, text="GOLD AI", style="SidebarTitle.TLabel").pack(anchor="w")
        ttk.Label(
            header, text="Purity Estimation", style="SidebarSub.TLabel"
        ).pack(anchor="w", pady=(3, 0))

        nav = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        nav.pack(fill="x", padx=10)

        for label, key in self.NAV_ITEMS:
            button = ttk.Button(
                nav, text=label, style="Nav.TButton",
                command=lambda page=key: self.show_page(page)
            )
            button.pack(fill="x", pady=2)
            self._nav_buttons[key] = button

        ttk.Frame(self.sidebar, style="Sidebar.TFrame").pack(
            fill="both", expand=True
        )

        note = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        note.pack(fill="x", padx=18, pady=18)
        ttk.Label(
            note, text="ACADEMIC SIMULATION", style="SidebarSub.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            note, text="Synthetic dataset • ML regression",
            style="SidebarSub.TLabel"
        ).pack(anchor="w", pady=(4, 0))

    def _build_main_area(self):
        self.header = ttk.Frame(self.main_area, style="Main.TFrame")
        self.header.pack(fill="x", padx=28, pady=(22, 12))

        self.page_title = ttk.Label(
            self.header, text="", style="PageTitle.TLabel"
        )
        self.page_title.pack(anchor="w")
        self.page_subtitle = ttk.Label(
            self.header, text="", style="PageSubtitle.TLabel"
        )
        self.page_subtitle.pack(anchor="w", pady=(3, 0))

        self.content = ttk.Frame(self.main_area, style="Main.TFrame")
        self.content.pack(fill="both", expand=True, padx=28, pady=(0, 14))

    def _build_status_bar(self):
        bar = ttk.Frame(self.main_area, style="Main.TFrame")
        bar.pack(fill="x", padx=28, pady=(0, 12))
        ttk.Label(
            bar, textvariable=self.status_var, style="Status.TLabel"
        ).pack(side="left", fill="x", expand=True)
        ttk.Label(
            bar, text="Synthetic/Simulated Sample Dataset • Academic Use",
            style="PageSubtitle.TLabel"
        ).pack(side="right")

    # ------------------------------------------------------------- helpers
    def _clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()
        self._images.clear()

    def _page_header(self, title, subtitle):
        self.page_title.config(text=title)
        self.page_subtitle.config(text=subtitle)

    def _card(self, parent, title, value=""):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=16)
        ttk.Label(frame, text=title.upper(), style="CardTitle.TLabel").pack(
            anchor="w"
        )
        value_label = ttk.Label(frame, text=value, style="CardValue.TLabel")
        value_label.pack(anchor="w", pady=(6, 0))
        return frame, value_label

    def _make_scrollable(self, parent):
        outer = ttk.Frame(parent, style="Main.TFrame")
        canvas = tk.Canvas(
            outer, highlightthickness=0, bg="#f5f7fb", borderwidth=0
        )
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, style="Main.TFrame")
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def resize_inner(event):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
                canvas.itemconfigure(window_id, width=event.width)
            except Exception:
                pass

        inner.bind("<Configure>", resize_inner)
        canvas.bind("<Configure>", lambda event: resize_inner(event))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return outer, inner

    def _load_metrics(self):
        try:
            return load_metrics()
        except (FileNotFoundError, OSError, ValueError):
            return None

    def _load_dataset(self):
        if not config.DATASET_PATH.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(config.DATASET_PATH)
        except Exception:
            return pd.DataFrame()

    def _format_metric(self, value, digits=3):
        try:
            return f"{float(value):.{digits}f}"
        except (TypeError, ValueError):
            return "—"

    def _show_tree(self, parent, dataframe, height=10, max_columns=None):
        if dataframe is None:
            dataframe = pd.DataFrame()
        columns = list(dataframe.columns)
        if max_columns:
            columns = columns[:max_columns]
        tree = ttk.Treeview(
            parent, columns=columns, show="headings", height=height
        )
        for column in columns:
            tree.heading(column, text=str(column))
            tree.column(column, width=125, anchor="center")
        if not dataframe.empty:
            for _, row in dataframe.iterrows():
                values = []
                for column in columns:
                    value = row[column]
                    if pd.isna(value):
                        values.append("")
                    elif isinstance(value, float):
                        values.append(f"{value:.3f}")
                    else:
                        values.append(value)
                tree.insert("", "end", values=values)

        ybar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        xbar = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        return tree

    def _load_graph_image(self, parent, path, max_width=920, max_height=500):
        """Display each evaluation graph responsively so no chart is clipped."""
        if not path.exists():
            ttk.Label(
                parent,
                text="Graph not found. Run  python -m src.main train",
                style="Body.TLabel",
            ).pack(pady=30)
            return

        try:
            source = Image.open(path).convert("RGB")
            holder = ttk.Frame(parent, style="Main.TFrame")
            holder.pack(fill="both", expand=True, padx=8, pady=8)
            holder.columnconfigure(0, weight=1)
            holder.rowconfigure(0, weight=1)

            label = ttk.Label(holder, anchor="center")
            label.grid(row=0, column=0, sticky="nsew")

            def fit_graph(_event=None):
                available_w = max(360, holder.winfo_width() - 16)
                available_h = max(260, holder.winfo_height() - 16)
                width, height = source.size
                scale = min(available_w / width, available_h / height, 1.0, max_width / width, max_height / height)
                new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
                resized = source.resize(new_size, Image.Resampling.LANCZOS) if scale < 1.0 else source.copy()
                photo = ImageTk.PhotoImage(resized)
                label.configure(image=photo)
                label.image = photo
                self._images.append(photo)
                # Keep only the most recent graph images to avoid unnecessary memory growth.
                if len(self._images) > 20:
                    del self._images[:-20]

            holder.bind("<Configure>", fit_graph)
            holder.after(50, fit_graph)
        except Exception as error:
            ttk.Label(
                parent,
                text=f"Could not display graph:\n{error}",
                style="Body.TLabel",
            ).pack(pady=30)

    # ----------------------------------------------------------- navigation
    def show_page(self, page):
        pages = {
            "dashboard": (
                "Dashboard",
                "Overview of your gold-purity estimation system",
                self._build_dashboard,
            ),
            "analysis": (
                "Gold Sample Analysis",
                "Enter measurement values and generate a real ML prediction",
                self._build_analysis,
            ),
            "analytics": (
                "Visual Analytics",
                "Explore the existing model evaluation graphs and metrics",
                self._build_analytics,
            ),
            "history": (
                "Prediction History",
                "Review predictions saved by the application",
                self._build_history,
            ),
            "dataset": (
                "Dataset Explorer",
                "Inspect the synthetic dataset used by the academic simulation",
                self._build_dataset,
            ),
            "reports": (
                "Reports",
                "Generate and review PDF prediction reports",
                self._build_reports,
            ),
            "system": (
                "Model & System",
                "Model selection, performance and project configuration",
                self._build_system,
            ),
            "assistant": (
                "AI Project Assistant",
                "Ask grounded questions about the project or run a real ML prediction",
                self._build_assistant,
            ),
            "about": (
                "About the Project",
                "Purpose, workflow, technologies and academic disclaimer",
                self._build_about,
            ),
        }
        if page not in pages:
            page = "dashboard"

        title, subtitle, builder = pages[page]
        self._clear_content()
        self._page_header(title, subtitle)
        self._pages[page] = True
        for key, button in self._nav_buttons.items():
            try:
                button.configure(
                    style="NavActive.TButton" if key == page else "Nav.TButton"
                )
            except Exception:
                pass
        builder()
        self.status_var.set(f"{title} loaded")

    # ------------------------------------------------------------- dashboard
    def _build_dashboard(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        metrics = self._load_metrics()
        data = self._load_dataset()
        history = self.history.load()
        best_model = metrics.get("best_model", "—") if metrics else "—"
        test_rmse = (
            metrics.get("models", {}).get(best_model, {}).get("rmse")
            if metrics else None
        )

        cards = ttk.Frame(body, style="Main.TFrame")
        cards.pack(fill="x", pady=(0, 14))
        card_data = [
            ("Dataset Samples", str(len(data)) if not data.empty else "—"),
            ("Selected Model", best_model),
            ("Best Test RMSE", self._format_metric(test_rmse)),
            ("Saved Predictions", str(len(history)) if not history.empty else "0"),
        ]
        for i, (title, value) in enumerate(card_data):
            card, _ = self._card(cards, title, value)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0))
            cards.columnconfigure(i, weight=1)

        quick = ttk.Frame(body, style="Main.TFrame")
        quick.pack(fill="x", pady=(0, 14))
        ttk.Label(quick, text="Quick Actions", style="Section.TLabel").pack(
            anchor="w", pady=(0, 8)
        )
        action_card = ttk.Frame(quick, style="Card.TFrame", padding=15)
        action_card.pack(fill="x")
        for i, (label, command) in enumerate([
            ("New Gold Analysis", lambda: self.show_page("analysis")),
            ("Load Dataset Sample", self.on_load_sample),
            ("View Analytics", lambda: self.show_page("analytics")),
            ("Prediction History", lambda: self.show_page("history")),
        ]):
            ttk.Button(
                action_card, text=label,
                style="Gold.TButton" if i == 0 else "Secondary.TButton",
                command=command,
            ).grid(row=0, column=i, padx=5, pady=2, sticky="ew")
            action_card.columnconfigure(i, weight=1)

        overview = ttk.Frame(body, style="Main.TFrame")
        overview.pack(fill="x")
        left = ttk.Frame(overview, style="Card.TFrame", padding=16)
        right = ttk.Frame(overview, style="Card.TFrame", padding=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        overview.columnconfigure(0, weight=1)
        overview.columnconfigure(1, weight=1)

        ttk.Label(left, text="Current Model", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            left, text=best_model, style="CardValue.TLabel"
        ).pack(anchor="w", pady=(5, 8))
        selection = metrics.get("selection_criterion", "Not available") if metrics else "Not available"
        dataset_name = metrics.get("dataset", config.DATASET_LABEL) if metrics else config.DATASET_LABEL
        ttk.Label(
            left, text=f"Selection: {selection}", style="Body.TLabel",
            wraplength=450
        ).pack(anchor="w")
        ttk.Label(
            left, text=f"Dataset: {dataset_name}", style="Muted.TLabel",
            wraplength=450
        ).pack(anchor="w", pady=(6, 0))

        ttk.Label(right, text="Recent Predictions", style="CardTitle.TLabel").pack(anchor="w")
        if history.empty:
            ttk.Label(
                right,
                text="No predictions saved yet.\nRun a sample analysis and choose Save Result.",
                style="Body.TLabel",
                justify="left",
            ).pack(anchor="w", pady=(12, 5))
        else:
            recent = history.tail(5).iloc[::-1]
            for _, row in recent.iterrows():
                text = (
                    f"{row.get('Date/Time', '')}   •   "
                    f"{row.get('Predicted Purity', '')}%   •   "
                    f"{row.get('Model Used', '')}"
                )
                ttk.Label(right, text=text, style="Body.TLabel").pack(
                    anchor="w", pady=3
                )

        disclaimer = ttk.Label(
            body,
            text="  " + config.DISCLAIMER,
            style="Disclaimer.TLabel",
            wraplength=950,
            justify="left",
        )
        disclaimer.pack(fill="x", pady=(16, 8))

    # --------------------------------------------------------------- analysis
    def _build_analysis(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        top = ttk.Frame(body, style="Main.TFrame")
        top.pack(fill="x", pady=(0, 12))
        ttk.Label(
            top,
            text="Sample measurements",
            style="Section.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            top,
            text="Use the same eight inputs used by the trained pipeline. "
                 "A reference purity is optional and is only used for comparison.",
            style="PageSubtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        form = ttk.Frame(body, style="Card.TFrame", padding=18)
        form.pack(fill="x")
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        for index, name in enumerate(config.FEATURE_COLUMNS):
            rule = config.FIELD_RULES[name]
            col = 0 if index < 4 else 2
            row = index if index < 4 else index - 4
            label = f"{rule.label} ({rule.unit})" if rule.unit else rule.label
            ttk.Label(
                form, text=label, style="Body.TLabel"
            ).grid(row=row, column=col, sticky="w", padx=(0, 8), pady=7)
            ttk.Entry(
                form, textvariable=self.input_vars[name], width=24
            ).grid(row=row, column=col + 1, sticky="ew", padx=(0, 22), pady=7)

        ref_row = 4
        ttk.Label(
            form, text="Reference Purity (%) — optional", style="Body.TLabel"
        ).grid(row=ref_row, column=0, sticky="w", pady=(12, 7))
        ttk.Entry(
            form, textvariable=self.reference_input_var, width=24
        ).grid(row=ref_row, column=1, sticky="ew", padx=(0, 22), pady=(12, 7))

        actions = ttk.Frame(body, style="Main.TFrame")
        actions.pack(fill="x", pady=12)
        buttons = [
            ("Predict Purity", self.on_predict, "Gold.TButton"),
            ("Load Dataset Sample", self.on_load_sample, "Secondary.TButton"),
            ("Clear", self.on_clear, "Secondary.TButton"),
            ("Save Result", self.on_save, "Secondary.TButton"),
            ("Generate PDF", self.on_generate_report, "Secondary.TButton"),
        ]
        for i, (label, command, style) in enumerate(buttons):
            ttk.Button(
                actions, text=label, command=command, style=style
            ).grid(row=0, column=i, padx=(0, 7), sticky="ew")
            actions.columnconfigure(i, weight=1)

        result = ttk.Frame(body, style="Card.TFrame", padding=18)
        result.pack(fill="x", pady=(0, 12))
        ttk.Label(result, text="Prediction Result", style="CardTitle.TLabel").pack(
            anchor="w"
        )
        result_grid = ttk.Frame(result, style="Card.TFrame")
        result_grid.pack(fill="x", pady=(9, 0))
        values = [
            ("Predicted Purity", self.predicted_display_var),
            ("Reference Purity", self.reference_display_var),
            ("Absolute Difference", self.difference_display_var),
            ("Selected Model", self.model_display_var),
        ]
        for i, (label, var) in enumerate(values):
            cell = ttk.Frame(result_grid, style="Card.TFrame")
            cell.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            result_grid.columnconfigure(i, weight=1)
            ttk.Label(cell, text=label.upper(), style="CardTitle.TLabel").pack(
                anchor="w"
            )
            ttk.Label(
                cell,
                textvariable=var,
                style="CardValue.TLabel",
                wraplength=240,
                justify="left",
            ).pack(anchor="w", fill="x", pady=(5, 0))

        ttk.Label(
            body,
            text="Tip: Load Dataset Sample gives you a held-out synthetic sample "
                 "with a known reference purity, useful for demonstrating the prediction flow.",
            style="PageSubtitle.TLabel",
            wraplength=950,
        ).pack(anchor="w", pady=(2, 8))

    # -------------------------------------------------------------- analytics
    def _build_analytics(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        metrics = self._load_metrics()
        if not metrics:
            ttk.Label(
                body,
                text="Model metrics are not available. Run  python -m src.main train",
                style="Body.TLabel",
            ).pack(anchor="w", pady=20)
            return

        summary = ttk.Frame(body, style="Card.TFrame", padding=15)
        summary.pack(fill="x", pady=(0, 12))
        ttk.Label(
            summary,
            text=f"Selected model: {metrics.get('best_model', '—')}   •   "
                 f"Selection: {metrics.get('selection_criterion', '—')}",
            style="Body.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            summary,
            text=f"Dataset: {metrics.get('dataset', config.DATASET_LABEL)}   •   "
                 f"Train rows: {metrics.get('train_rows', '—')}   •   "
                 f"Test rows: {metrics.get('test_rows', '—')}",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(5, 0))

        columns = ("Model", "MAE", "MSE", "RMSE", "R²")
        table = ttk.Treeview(summary, columns=columns, show="headings", height=3)
        for col in columns:
            table.heading(col, text=col)
            table.column(col, width=150 if col == "Model" else 105, anchor="center")
        for name, values in metrics.get("models", {}).items():
            table.insert(
                "", "end",
                values=(
                    name,
                    self._format_metric(values.get("mae"), 4),
                    self._format_metric(values.get("mse"), 4),
                    self._format_metric(values.get("rmse"), 4),
                    self._format_metric(values.get("r2"), 4),
                ),
            )
        table.pack(fill="x", pady=(12, 0))

        ttk.Label(
            body, text="Model Evaluation Graphs", style="Section.TLabel"
        ).pack(anchor="w", pady=(5, 8))

        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True, pady=(0, 10))
        for title, filename in GRAPH_FILES.items():
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=title)
            self._load_graph_image(tab, config.GRAPHS_DIR / filename)

    # --------------------------------------------------------------- history
    def _build_history(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        table_card = ttk.Frame(body, style="Card.TFrame", padding=14)
        table_card.pack(fill="both", expand=True)

        history = self.history.load()
        if history.empty:
            ttk.Label(
                table_card,
                text="No saved predictions yet. Go to Gold Sample Analysis and "
                     "save a prediction.",
                style="Body.TLabel",
            ).pack(anchor="w", pady=15)
            return

        ttk.Label(
            table_card,
            text=f"{len(history)} saved prediction(s)",
            style="CardTitle.TLabel",
        ).pack(anchor="w", pady=(0, 10))
        table_area = ttk.Frame(table_card, style="Card.TFrame")
        table_area.pack(fill="both", expand=True)
        self._show_tree(table_area, history, height=12)

    # --------------------------------------------------------------- dataset
    def _build_dataset(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        data = self._load_dataset()
        if data.empty:
            ttk.Label(
                body,
                text="Dataset not found. Run  python -m src.main generate",
                style="Body.TLabel",
            ).pack(anchor="w", pady=20)
            return

        cards = ttk.Frame(body, style="Main.TFrame")
        cards.pack(fill="x", pady=(0, 12))
        stats = [
            ("Rows", len(data)),
            ("Features", len(config.FEATURE_COLUMNS)),
            ("Purity Min", f"{data[config.TARGET_COLUMN].min():.2f}%"),
            ("Purity Max", f"{data[config.TARGET_COLUMN].max():.2f}%"),
            ("Purity Mean", f"{data[config.TARGET_COLUMN].mean():.2f}%"),
        ]
        for i, (title, value) in enumerate(stats):
            card, _ = self._card(cards, title, str(value))
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0))
            cards.columnconfigure(i, weight=1)

        ttk.Label(
            body, text="Dataset Preview", style="Section.TLabel"
        ).pack(anchor="w", pady=(2, 7))
        table_card = ttk.Frame(body, style="Card.TFrame", padding=12)
        table_card.pack(fill="both", expand=True)
        table_area = ttk.Frame(table_card, style="Card.TFrame")
        table_area.pack(fill="both", expand=True)
        self._show_tree(table_area, data.head(100), height=12)

        ttk.Label(
            body,
            text=f"Source: {config.DATASET_PATH}  •  {config.DATASET_LABEL}",
            style="PageSubtitle.TLabel",
        ).pack(anchor="w", pady=(8, 0))

    # ---------------------------------------------------------------- reports
    def _build_reports(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        top = ttk.Frame(body, style="Card.TFrame", padding=16)
        top.pack(fill="x", pady=(0, 12))
        ttk.Label(
            top, text="Create a report from the latest prediction",
            style="CardTitle.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            top,
            text=(
                "The PDF uses the existing report_generator module and includes "
                "sample inputs, prediction, optional reference comparison and model metrics."
            ),
            style="Body.TLabel", wraplength=900
        ).pack(anchor="w", pady=(7, 10))
        ttk.Button(
            top, text="Generate PDF Report",
            style="Gold.TButton", command=self.on_generate_report
        ).pack(anchor="w")

        ttk.Label(
            body, text="Existing PDF Reports", style="Section.TLabel"
        ).pack(anchor="w", pady=(4, 8))

        files = sorted(
            config.REPORTS_DIR.glob("*.pdf"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )
        if not files:
            ttk.Label(
                body, text="No PDF reports have been generated yet.",
                style="Body.TLabel"
            ).pack(anchor="w")
        else:
            for path in files:
                card = ttk.Frame(body, style="Card.TFrame", padding=10)
                card.pack(fill="x", pady=4)
                info = ttk.Frame(card, style="Card.TFrame")
                info.pack(side="left", fill="x", expand=True)
                name = ttk.Label(
                    info, text=path.name, style="Body.TLabel", cursor="hand2"
                )
                name.pack(anchor="w")
                name.bind("<Double-Button-1>", lambda _e, p=path: self._open_pdf(p))
                ttk.Label(
                    info, text=str(path), style="Muted.TLabel"
                ).pack(anchor="w", pady=(3, 0))
                ttk.Button(
                    card, text="Open PDF", style="Secondary.TButton",
                    command=lambda p=path: self._open_pdf(p)
                ).pack(side="right", padx=(10, 0))

        ttk.Label(
            body,
            text=f"Reports folder: {config.REPORTS_DIR}",
            style="PageSubtitle.TLabel",
        ).pack(anchor="w", pady=(10, 0))

    # --------------------------------------------------------------- system
    def _build_system(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        metrics = self._load_metrics()
        info = ttk.Frame(body, style="Card.TFrame", padding=16)
        info.pack(fill="x", pady=(0, 12))
        ttk.Label(info, text="Model Configuration", style="CardTitle.TLabel").pack(
            anchor="w"
        )

        rows = [
            ("Selected model", metrics.get("best_model", "Not trained") if metrics else "Not trained"),
            ("Selection rule", metrics.get("selection_criterion", "—") if metrics else "—"),
            ("Dataset", metrics.get("dataset", config.DATASET_LABEL) if metrics else config.DATASET_LABEL),
            ("Train rows", metrics.get("train_rows", "—") if metrics else "—"),
            ("Test rows", metrics.get("test_rows", "—") if metrics else "—"),
            ("Features", ", ".join(config.FEATURE_COLUMNS)),
            ("Model file", str(config.MODEL_PATH)),
            ("Metrics file", str(config.METRICS_PATH)),
        ]
        for label, value in rows:
            row = ttk.Frame(info, style="Card.TFrame")
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label, style="CardTitle.TLabel", width=18).pack(
                side="left", anchor="w"
            )
            ttk.Label(
                row, text=str(value), style="Body.TLabel", wraplength=800
            ).pack(side="left", anchor="w")

        ttk.Label(
            body, text="Model Performance", style="Section.TLabel"
        ).pack(anchor="w", pady=(4, 8))
        performance = ttk.Frame(body, style="Card.TFrame", padding=12)
        performance.pack(fill="x")

        if metrics:
            columns = ("Model", "MAE", "MSE", "RMSE", "R²")
            table = ttk.Treeview(performance, columns=columns, show="headings", height=3)
            for col in columns:
                table.heading(col, text=col)
                table.column(col, width=150 if col == "Model" else 110, anchor="center")
            for name, values in metrics.get("models", {}).items():
                table.insert(
                    "", "end",
                    values=(
                        name,
                        self._format_metric(values.get("mae"), 4),
                        self._format_metric(values.get("mse"), 4),
                        self._format_metric(values.get("rmse"), 4),
                        self._format_metric(values.get("r2"), 4),
                    ),
                )
            table.pack(fill="x")
        else:
            ttk.Label(
                performance,
                text="No metrics available. Train the model first.",
                style="Body.TLabel"
            ).pack(anchor="w")

        ttk.Label(
            body, text="Training and GUI Commands", style="Section.TLabel"
        ).pack(anchor="w", pady=(16, 8))
        commands = ttk.Frame(body, style="Card.TFrame", padding=14)
        commands.pack(fill="x")
        for command in [
            "python -m src.main generate",
            "python -m src.main train",
            "python -m src.main all",
            "python -m src.main gui",
            "python -m unittest discover -s tests -t . -v",
        ]:
            ttk.Label(
                commands, text=command, style="Body.TLabel"
            ).pack(anchor="w", pady=3)

    # ---------------------------------------------------------- AI assistant
    def _build_assistant(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        intro = ttk.Frame(body, style="Card.TFrame", padding=18)
        intro.pack(fill="x", pady=(0, 12))
        ttk.Label(intro, text="GoldAI Project Assistant", style="CardValue.TLabel").pack(anchor="w")
        ttk.Label(
            intro,
            text=(
                "The assistant is a live, project-grounded helper. It reads the current dataset, "
                "model metrics and prediction pipeline. It can answer project questions and run "
                "real purity predictions from the saved ML model."
            ),
            style="Body.TLabel", wraplength=950, justify="left"
        ).pack(anchor="w", pady=(6, 0))

        quick = ttk.Frame(body, style="Card.TFrame", padding=14)
        quick.pack(fill="x", pady=(0, 12))
        ttk.Label(quick, text="Try the floating assistant", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            quick,
            text="Use the AI button at the bottom-right. Drag its title bar to move it anywhere on the screen.",
            style="Body.TLabel", wraplength=950
        ).pack(anchor="w", pady=(6, 10))
        ttk.Button(
            quick, text="Open AI Assistant", style="Gold.TButton",
            command=self._show_floating_assistant
        ).pack(anchor="w")

        examples = ttk.Frame(body, style="Card.TFrame", padding=14)
        examples.pack(fill="x")
        ttk.Label(examples, text="Example questions", style="CardTitle.TLabel").pack(anchor="w")
        for text in (
            "Which model is best and why?",
            "How many samples are in the dataset?",
            "Explain the project workflow.",
            "What are the limitations?",
            "Predict purity for density 19.039, copper 0.158, silver 0, zinc 0, nickel 0.156, xrf 100, temperature 23.3, weight 10.71",
        ):
            ttk.Label(examples, text="• " + text, style="Body.TLabel", wraplength=950).pack(anchor="w", pady=3)

        self._show_floating_assistant()

    def _create_floating_assistant(self):
        """Create a modern round, draggable AI launcher at the bottom-right."""
        self.ai_window = None
        self._assistant_drag = None
        self._launcher_drag = None
        self._launcher_moved = False

        # A Canvas gives us a genuinely round launcher (Tk buttons remain rectangular).
        self.ai_launcher = tk.Canvas(
            self.root, width=64, height=64, highlightthickness=0,
            bd=0, bg="#f5f7fb", cursor="hand2"
        )
        self.ai_launcher.place(relx=0.975, rely=0.94, anchor="se", width=64, height=64)
        self._draw_ai_launcher()
        self.ai_launcher.bind("<ButtonPress-1>", self._launcher_press)
        self.ai_launcher.bind("<B1-Motion>", self._launcher_motion)
        self.ai_launcher.bind("<ButtonRelease-1>", self._launcher_release)

    def _draw_ai_launcher(self):
        self.ai_launcher.delete("all")
        self.ai_launcher.create_oval(3, 4, 61, 62, fill="#6D4AFF", outline="#4F35C7", width=2)
        self.ai_launcher.create_text(32, 32, text="AI", fill="white", font=("Segoe UI", 13, "bold"))

    def _launcher_press(self, event):
        self._launcher_drag = (event.x_root, event.y_root, self.ai_launcher.winfo_x(), self.ai_launcher.winfo_y())
        self._launcher_moved = False

    def _launcher_motion(self, event):
        if not self._launcher_drag:
            return
        sx, sy, x, y = self._launcher_drag
        dx = event.x_root - sx
        dy = event.y_root - sy
        if abs(dx) > 4 or abs(dy) > 4:
            self._launcher_moved = True
        new_x = max(0, min(self.root.winfo_width() - 64, x + dx))
        new_y = max(0, min(self.root.winfo_height() - 64, y + dy))
        self.ai_launcher.place_configure(x=new_x, y=new_y, anchor="nw")

    def _launcher_release(self, _event):
        if not self._launcher_moved:
            self._show_floating_assistant()
        self._launcher_drag = None

    def _show_floating_assistant(self):
        if self.ai_window is not None and self.ai_window.winfo_exists():
            self.ai_window.deiconify()
            self.ai_window.lift()
            return

        win = tk.Toplevel(self.root)
        self.ai_window = win
        win.title("GoldAI Assistant")
        win.geometry("390x470")
        win.minsize(340, 400)
        win.configure(bg="#f5f7fb")
        win.overrideredirect(True)
        win.protocol("WM_DELETE_WINDOW", self._hide_floating_assistant)

        # Open next to the current round launcher, so dragging the launcher also changes
        # where the assistant appears.
        self.root.update_idletasks()
        win.update_idletasks()
        lx = self.root.winfo_rootx() + self.ai_launcher.winfo_x()
        ly = self.root.winfo_rooty() + self.ai_launcher.winfo_y()
        x = max(10, lx + self.ai_launcher.winfo_width() - win.winfo_width())
        y = max(10, ly - win.winfo_height() - 10)
        if y < 10:
            y = min(self.root.winfo_rooty() + self.root.winfo_height() - win.winfo_height() - 10, ly + 70)
        win.geometry(f"+{x}+{max(10, y)}")

        title = tk.Frame(win, bg="#6D4AFF", height=46, cursor="fleur")
        title.pack(fill="x")
        tk.Label(title, text="🤖  GoldAI Assistant", bg="#6D4AFF", fg="white",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=12, pady=10)
        tk.Button(title, text="×", command=self._hide_floating_assistant, bg="#6D4AFF",
                  fg="white", activebackground="#5A3BD6", activeforeground="white",
                  relief="flat", bd=0, font=("Segoe UI", 14, "bold"), cursor="hand2").pack(side="right", padx=8)

        title.bind("<ButtonPress-1>", self._ai_drag_start)
        title.bind("<B1-Motion>", self._ai_drag_move)
        for child in title.winfo_children():
            if isinstance(child, tk.Label):
                child.bind("<ButtonPress-1>", self._ai_drag_start)
                child.bind("<B1-Motion>", self._ai_drag_move)

        body = tk.Frame(win, bg="#f5f7fb")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        self.ai_chat = tk.Text(body, wrap="word", state="disabled", bg="white", fg="#172033",
                               relief="flat", font=("Segoe UI", 9), padx=9, pady=9)
        chat_bar = ttk.Scrollbar(body, orient="vertical", command=self.ai_chat.yview)
        self.ai_chat.configure(yscrollcommand=chat_bar.set)
        self.ai_chat.grid(row=0, column=0, sticky="nsew")
        chat_bar.grid(row=0, column=1, sticky="ns")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        quick = tk.Frame(body, bg="#f5f7fb")
        quick.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(7, 6))
        for i, prompt in enumerate(("Best model?", "Dataset size?", "Workflow?", "Limitations?")):
            tk.Button(quick, text=prompt, command=lambda p=prompt: self._floating_ask(p),
                      bg="#eeeaff", fg="#4F35C7", relief="flat", bd=0,
                      font=("Segoe UI", 8, "bold"), cursor="hand2").grid(
                          row=0, column=i, padx=2, sticky="ew")
            quick.columnconfigure(i, weight=1)

        entry = tk.Frame(body, bg="#f5f7fb")
        entry.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.ai_entry = ttk.Entry(entry)
        self.ai_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(entry, text="Ask", style="Gold.TButton", command=self._floating_submit).pack(side="right")
        self.ai_entry.bind("<Return>", lambda _e: self._floating_submit())
        self.ai_entry.focus_set()

        self._floating_append("GoldAI", "Ready. Ask me about the project, dataset, models, metrics, workflow, reports, history or give eight measurements for a real ML prediction.")

    def _hide_floating_assistant(self):
        if self.ai_window is not None and self.ai_window.winfo_exists():
            self.ai_window.withdraw()

    def _ai_drag_start(self, event):
        if self.ai_window is None:
            return
        self._assistant_drag = (event.x_root, event.y_root, self.ai_window.winfo_x(), self.ai_window.winfo_y())

    def _ai_drag_move(self, event):
        if not self._assistant_drag or self.ai_window is None:
            return
        sx, sy, wx, wy = self._assistant_drag
        self.ai_window.geometry(f"+{wx + event.x_root - sx}+{wy + event.y_root - sy}")

    def _floating_append(self, speaker, text):
        if not hasattr(self, "ai_chat") or not self.ai_chat.winfo_exists():
            return
        self.ai_chat.configure(state="normal")
        self.ai_chat.insert("end", f"{speaker}:\n{text}\n\n")
        self.ai_chat.see("end")
        self.ai_chat.configure(state="disabled")

    def _floating_ask(self, prompt):
        if hasattr(self, "ai_entry") and self.ai_entry.winfo_exists():
            self.ai_entry.delete(0, "end")
        self._floating_submit(prompt)

    def _floating_submit(self, prompt=None):
        if prompt is None:
            prompt = self.ai_entry.get().strip() if hasattr(self, "ai_entry") else ""
        if not prompt:
            return
        self._floating_append("You", prompt)
        try:
            answer = self.assistant.answer(prompt)
        except Exception as error:
            answer = f"I could not complete that request: {error}"
        self._floating_append("GoldAI", answer)
        if hasattr(self, "ai_entry") and self.ai_entry.winfo_exists():
            self.ai_entry.delete(0, "end")
        self.status_var.set("AI Assistant answered using project-grounded data.")


    # ---------------------------------------------------------------- about
    def _build_about(self):
        outer, body = self._make_scrollable(self.content)
        outer.pack(fill="both", expand=True)

        cards = [
            (
                "Project Objective",
                "Estimate gold purity from eight measurement-like inputs using "
                "regression models on a synthetic academic dataset."
            ),
            (
                "Machine Learning",
                "Linear Regression, Decision Tree Regressor and Random Forest "
                "Regressor are evaluated with MAE, MSE, RMSE and R². The model "
                "with the lowest test RMSE is selected automatically."
            ),
            (
                "Workflow",
                "CSV Dataset → Validation → Preprocessing → Train/Test Split → "
                "Model Evaluation → Best Model → Saved Pipeline → GUI Prediction."
            ),
            (
                "Technology",
                "Python, Pandas, NumPy, Scikit-learn, Tkinter, Matplotlib, "
                "Joblib and ReportLab."
            ),
        ]
        for title, text in cards:
            card = ttk.Frame(body, style="Card.TFrame", padding=17)
            card.pack(fill="x", pady=5)
            ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(
                card, text=text, style="Body.TLabel", wraplength=950,
                justify="left"
            ).pack(anchor="w", pady=(6, 0))

        disclaimer = ttk.Frame(body, style="Disclaimer.TLabel", padding=12)
        disclaimer.pack(fill="x", pady=(14, 6))
        ttk.Label(
            disclaimer,
            text=config.DISCLAIMER + " The dataset is synthetic/simulated and "
                 "the application is intended for academic demonstration.",
            style="Disclaimer.TLabel",
            wraplength=950, justify="left"
        ).pack(anchor="w")

    # ---------------------------------------------------------- prediction
    def _get_model(self):
        """Load the saved model once and reuse it (no retraining)."""
        if self._model is None:
            self._model = MLModel.load()
        return self._model

    def _read_inputs(self):
        return {name: var.get() for name, var in self.input_vars.items()}

    def _show_result(self, prediction):
        # Keep the result values concise because the card titles already
        # identify each metric. This prevents long labels from being clipped
        # when the four result cards share the available window width.
        predicted = f"{prediction.predicted_purity:.2f} %"
        self.predicted_var.set(f"Predicted Gold Purity: {predicted}")
        self.predicted_display_var.set(predicted)
        if prediction.reference_purity is None:
            self.reference_var.set("Reference Purity: N/A")
            self.reference_display_var.set("N/A")
            self.difference_var.set("Difference: N/A")
            self.difference_display_var.set("N/A")
        else:
            reference = f"{prediction.reference_purity:.2f} %"
            difference = f"{prediction.difference:.2f} %"
            self.reference_var.set(f"Reference Purity: {reference}")
            self.reference_display_var.set(reference)
            self.difference_var.set(f"Difference: {difference}")
            self.difference_display_var.set(difference)
        self.model_var.set(f"Selected Model: {prediction.model_name}")
        self.model_display_var.set(prediction.model_name)

    def on_predict(self):
        try:
            prediction = run_prediction(
                self._read_inputs(),
                self.reference_input_var.get(),
                model=self._get_model(),
            )
        except InputValidationError as error:
            messagebox.showerror("Invalid Input", "\n".join(error.errors))
            self.status_var.set("Prediction not made: please correct the input.")
            return
        except ModelNotFoundError as error:
            messagebox.showerror("Model Not Found", str(error))
            self.status_var.set("No trained model found. Train the model first.")
            return
        except Exception as error:
            messagebox.showerror("Unexpected Error", f"Prediction failed:\n{error}")
            self.status_var.set("Prediction failed.")
            return

        self.last_prediction = prediction
        self._show_result(prediction)
        if prediction.warnings:
            self.status_var.set(" • ".join(prediction.warnings))
        else:
            self.status_var.set(
                "Prediction complete. Save the result or generate a PDF report."
            )

    def on_clear(self):
        for var in self.input_vars.values():
            var.set("")
        self.reference_input_var.set("")
        self.last_prediction = None
        self.predicted_var.set("Predicted Gold Purity: -")
        self.reference_var.set("Reference Purity: -")
        self.difference_var.set("Difference: -")
        self.model_var.set("Selected Model: -")
        self.predicted_display_var.set("-")
        self.reference_display_var.set("-")
        self.difference_display_var.set("-")
        self.model_display_var.set("-")
        self.status_var.set("Cleared. Enter sample values to predict.")

    def on_save(self):
        if self.last_prediction is None:
            messagebox.showwarning(
                "Nothing to Save", "Please click 'Predict Purity' first."
            )
            return
        try:
            self.history.save(self.last_prediction)
        except OSError as error:
            messagebox.showerror(
                "Save Failed", f"Could not write the history file:\n{error}"
            )
            return
        messagebox.showinfo(
            "Saved", f"Result saved to:\n{self.history.path}"
        )
        self.status_var.set("Result saved to prediction history.")

    def on_load_sample(self):
        """Fill the form with a random held-out sample and reference purity."""
        try:
            inputs, reference = get_random_test_sample()
        except (FileNotFoundError, ValueError) as error:
            messagebox.showerror("Sample Not Available", str(error))
            return
        for name, value in inputs.items():
            self.input_vars[name].set(f"{value:g}")
        self.reference_input_var.set(f"{reference:.2f}")
        self.status_var.set(
            "Held-out synthetic sample loaded. Click Predict Purity."
        )
        self.show_page("analysis")

    def _open_pdf(self, path):
        """Open a generated PDF with the user's default PDF application."""
        try:
            path = Path(path)
            if not path.exists():
                messagebox.showerror("PDF Not Found", f"The PDF no longer exists:\n{path}")
                return
            os.startfile(str(path))
            self.status_var.set(f"Opened PDF: {path.name}")
        except Exception as error:
            messagebox.showerror("Open PDF Failed", f"Could not open the PDF:\n{error}")

    def on_generate_report(self):
        if self.last_prediction is None:
            messagebox.showwarning(
                "No Result",
                "Please make a prediction first, then generate the PDF report.",
            )
            return
        try:
            path = generate_pdf_report(self.last_prediction)
        except Exception as error:
            messagebox.showerror(
                "Report Failed", f"Could not create the PDF report:\n{error}"
            )
            return
        messagebox.showinfo(
            "Report Created", f"PDF report saved to:\n{path}"
        )
        self.status_var.set("PDF report generated successfully.")
        self.show_page("reports")

    def on_view_history(self):
        """Compatibility action: show a useful message for an empty history."""
        table = self.history.load()
        if table.empty:
            messagebox.showinfo("Prediction History", "No saved predictions yet.")
            return
        self.show_page("history")

    def on_view_performance(self):
        """Compatibility action: navigate to the full analytics page."""
        self.show_page("analytics")

    def on_exit(self):
        self.root.destroy()


def run_app():
    root = tk.Tk()
    GoldPurityApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
