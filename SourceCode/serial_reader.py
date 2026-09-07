"""Background serial reader that parses simulator lines into sensor updates."""
import threading

import serial
from PySide6.QtCore import QObject, Signal

from . import config

# Serial parameter name -> database field name.
_PARAM_ALIASES = {"temp": "temperature", "hum": "humidity", "uv": "uv"}


def parse_reading(line):
    """Parse one protocol line into (node_id, {field: value}).

    Supported comma-separated formats:
        "<node>,<temp>"                 -> temperature only
        "<node>,<temp>,<hum>"           -> temperature + humidity
        "<node>,<temp>,<hum>,<uv>"      -> all three
        "<node>,<param>,<value>"        -> single field, param in {temp, hum, uv}

    Raises ValueError on any other input.
    """
    tokens = [t.strip() for t in line.split(",")]
    node_id = int(tokens[0])

    if len(tokens) == 3 and tokens[1].isalpha():
        field = _PARAM_ALIASES.get(tokens[1].lower())
        if field is None:
            raise ValueError(f"unknown parameter: {tokens[1]}")
        return node_id, {field: float(tokens[2])}

    if len(tokens) == 2:
        return node_id, {"temperature": float(tokens[1])}

    if len(tokens) == 3:
        return node_id, {"temperature": float(tokens[1]),
                         "humidity": float(tokens[2])}

    if len(tokens) == 4:
        return node_id, {"temperature": float(tokens[1]),
                         "humidity": float(tokens[2]),
                         "uv": float(tokens[3])}

    raise ValueError(f"invalid format: {line}")


class SerialReader(QObject):
    """Reads the serial port on a background thread and emits parsed updates.

    Signals are delivered to the GUI thread by Qt, so slots can safely touch
    widgets. Call start() once and stop() on shutdown.
    """

    reading = Signal(int, dict)  # node_id, {field: value}
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        try:
            port = serial.Serial(config.SERIAL_PORT, config.SERIAL_BAUDRATE,
                                 timeout=config.SERIAL_TIMEOUT)
        except serial.SerialException as exc:
            self.error.emit(f"Could not open {config.SERIAL_PORT}: {exc}")
            return

        try:
            while not self._stop.is_set():
                raw = port.readline().decode(errors="ignore").strip()
                if not raw:
                    continue
                if raw.lower() == "stop":
                    break
                try:
                    node_id, updates = parse_reading(raw)
                except ValueError as exc:
                    self.error.emit(str(exc))
                    continue
                if node_id in config.NODES:
                    self.reading.emit(node_id, updates)
        finally:
            port.close()