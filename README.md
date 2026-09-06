# Sensor Data Simulation and Map Visualization

A desktop tool that simulates sensor-data transmission over a virtual COM port
(values are changed from the Br@y terminal), stores each reading in MongoDB, and
visualizes both live and historical data. The map shows the latest values per
node (Folium + Qt WebEngine); the analysis view plots any parameter over a time
range (Matplotlib). Built with Python and PySide6.

## Requirements

- Python 3.10+
- A running MongoDB instance (default: `localhost:27017`)
- A virtual COM port pair (e.g. com0com on Windows) driven by the Br@y terminal

## Setup

1. Create and activate a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Start MongoDB.
4. Adjust `config.py` for your setup (serial port, MongoDB, node locations).
5. Run the app: `python main.py`

## Serial protocol

Each line sent to the port is comma-separated:

1. `<node>,<temp>` — set temperature only
2. `<node>,<temp>,<hum>` — set temperature and humidity
3. `<node>,<temp>,<hum>,<uv>` — set all three
4. `<node>,<param>,<value>` — set a single field, where `param` is `temp`, `hum`, or `uv`
5. `stop` — stops the reader loop

## Project layout

1. `config.py` — all settings and node definitions
2. `database.py` — MongoDB read/write helpers
3. `serial_reader.py` — serial port loop and line parsing
4. `map_window.py` — map page
5. `analysis_window.py` — analysis/chart page
6. `main.py` — entry point and page navigation
