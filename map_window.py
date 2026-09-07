"""Map page: shows the latest reading for each sensor node on a Folium map."""
import io
 
import folium
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Signal

import config
import database
from serial_reader import SerialReader

class MapWindow(QWidget):
    show_analysis=Signal()

    def __init__(self):
        super().__init__()
        # node_id -> {"temperature", "humidity", "uv"} or None
        self.node_data={node_id:None for node_id in config.NODES}
        self.load_from_database()

        self.build_ui()
        self.refresh_map()

        self.reader = SerialReader(self)
        self.reader.reading.connect(self.on_reading)
        self.reader.error.connect(lambda msg: print(f"[serial] {msg}"))
        self.reader.start()

    def build_ui(self):
        nav=QHBoxLayout()
        analysis_btn=QPushButton("Go to Analysis")
        analysis_btn.clicked.connect(self.show_analysis.emit)
        nav.addWidget(analysis_btn)
        nav.addStretch()

        self.web_view=QWebEngineView()

        layout=QVBoxLayout(self)
        layout.addLayout(nav)
        layout.addWidget(self.web_view)

    def load_from_database(self):
        latest=database.get_latest_per_node()
        for node_id,values in latest.items():
            if node_id in self.node_data:
                temperature, humidity, uv = values
                self.node_data[node_id]={
                "temperature": temperature,
                "humidity": humidity,
                "uv": uv,    
                }

    def on_reading(self,node_id,updates):
        current=self.node_data[node_id] or {
            "temperature" : None, "humidity": None, "uv":None
        }
        current.update(updates)
        self.node_data[node_id]=current
        database.save_reading(node_id,current["temperature"],
                              current["humidity"],current["uv"])
        self.refresh_map()

    def refresh_map(self):
        self.web_view.setHtml(self.render_map())

    def render_map(self):
        fmap=folium.Map(location=config.MAP_CENTER,zoom_start=config.MAP_ZOOM)
        for node_id, (lat,lon,label) in config.NODES.items():
            data=self.node_data[node_id]

            if data:
                popup = self.marker_popup(node_id,label,data)
                color="blue"
            else:
                popup = f"<b>{label} (Node {node_id})</b><br>No data"
                color = "gray"

            folium.Marker(
                location=[lat,lon],
                popup=folium.Popup(popup,max_width=300),
                icon=folium.Icon(color,icon="info-sign"),
                ).add_to(fmap)

        buffer =io.BytesIO()
        fmap.save(buffer,close_file=False)
        return buffer.getvalue().decode()

    def marker_popup(self, node_id, label, data):
        rows = "".join(
            f"<b>{r['timestamp']}</b><br>"
            f"T: {r['temperature']}°C, H: {r['humidity']}%, UV: {r['uv']}<br><hr>"
            for r in database.get_recent_readings(node_id)
        )
        history = (
            "<div style='max-height:200px;overflow-y:auto;"
            f"border:1px solid #ccc;padding:5px;'>{rows}</div>"
        )
        return f"""
            <h3>{label} (Node {node_id})</h3>
            Temperature: {data['temperature']}°C<br>
            Humidity: {data['humidity']}%<br>
            UV: {data['uv']}<br><br>
            <b>Last {config.HISTORY_LIMIT} readings:</b><br>
            {history}
        """

    def stop(self):
        self.reader.stop()
