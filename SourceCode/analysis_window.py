"""Analysis page: plot one parameter for one node over a time range."""
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QDateTimeEdit, QDialog, QDialogButtonBox, QCalendarWidget,
)
from PySide6.QtCore import QDateTime, QDate, Signal

from . import config
from . import database

# Label shown in the UI -> database field name.
_PARAMETERS = {"Temperature": "temperature",
               "Humidity": "humidity",
               "UV": "uv"}


class CalendarDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select a date")
        self.setModal(True)

        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate.currentDate())

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.calendar)
        layout.addWidget(buttons)

    def selected_date(self):
        return self.calendar.selectedDate()


class AnalysisWindow(QWidget):
    show_map = Signal()

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        nav = QHBoxLayout()
        map_btn = QPushButton("Go to Map")
        map_btn.clicked.connect(self.show_map.emit)
        nav.addWidget(map_btn)
        nav.addStretch()

        self.node_box = QComboBox()
        for node_id in sorted(config.NODES):
            self.node_box.addItem(str(node_id))

        self.param_box = QComboBox()
        self.param_box.addItems(_PARAMETERS.keys())

        range_layout = QVBoxLayout()
        self.from_edit = self._add_range_row(
            range_layout, "From:", QDateTime.currentDateTime().addDays(-1))
        self.to_edit = self._add_range_row(
            range_layout, "To:", QDateTime.currentDateTime())

        plot_btn = QPushButton("Show chart")
        plot_btn.clicked.connect(self.plot)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Node:"))
        controls.addWidget(self.node_box)
        controls.addWidget(QLabel("Parameter:"))
        controls.addWidget(self.param_box)
        controls.addLayout(range_layout)
        controls.addWidget(plot_btn)

        self.figure = Figure()
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout(self)
        layout.addLayout(nav)
        layout.addLayout(controls)
        layout.addWidget(self.canvas)

    def _add_range_row(self, parent, label, default_dt):
        edit = QDateTimeEdit(default_dt)
        edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        button = QPushButton("📅")
        button.clicked.connect(lambda: self._pick_date(edit))

        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addWidget(edit)
        row.addWidget(button)
        parent.addLayout(row)
        return edit

    def _pick_date(self, edit):
        dialog = CalendarDialog(self)
        if dialog.exec() == QDialog.Accepted:
            time = edit.dateTime().time()
            edit.setDateTime(QDateTime(dialog.selected_date(), time))

    def plot(self):
        node_id = int(self.node_box.currentText())
        param_label = self.param_box.currentText()
        field = _PARAMETERS[param_label]
        start = self.from_edit.dateTime().toPython()
        end = self.to_edit.dateTime().toPython()

        readings = database.get_readings_between(node_id, start, end)

        self.ax.clear()
        if not readings:
            self.ax.text(0.5, 0.5, "No data in this range",
                         ha="center", va="center")
        else:
            times = [r["timestamp"] for r in readings]
            values = [r[field] for r in readings]
            self.ax.plot(times, values, marker="o")
            self.ax.set_title(f"Node {node_id} — {param_label} over time")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel(param_label)
            self.ax.grid(True)
            self.figure.autofmt_xdate()
        self.canvas.draw()