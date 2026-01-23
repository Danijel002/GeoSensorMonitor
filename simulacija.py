import sys
import io
import time
import folium
import serial
import threading

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Signal, QObject
from bp import sacuvani_podaci, poslednje_vrednosti_svih_nodeova, poslednjih_10_vrednosti


class SignalHandler(QObject):
    mapa_azurirana = Signal(str)


class MapaProzor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Folium mapa")
        self.setGeometry(200, 200, 1000, 800)

        
        nav_layout = QHBoxLayout()
        dugme_analiza = QPushButton("Idi na Analizu")
        dugme_analiza.clicked.connect(self.otvori_analizu)
        nav_layout.addWidget(dugme_analiza)
        nav_layout.addStretch()

        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(nav_layout)  
        
        self.webView = QWebEngineView()
        main_layout.addWidget(self.webView)
        self.setLayout(main_layout)

        
        self.lokacije = {
            1: [45.254410, 19.842550],  # Novi Sad
            2: [44.815071, 20.460480],  # Beograd
            3: [43.316872, 21.894501],  # Niš
            4: [45.773979, 19.118759],  # Sombor
            5: [43.981270, 21.257441]   # Jagodina
        }

       
        self.node_data = {i: None for i in self.lokacije.keys()}
        self.ucitaj_iz_baze()

        
        self.signali = SignalHandler()
        self.signali.mapa_azurirana.connect(self.osvezi_mapu)

        
        self.ser_thread = threading.Thread(target=self.serial_loop, daemon=True)
        self.ser_thread.start()

        
        self.osvezi_mapu(self.generisi_mapu())

    
    def ucitaj_iz_baze(self):
        poslednji_podaci = poslednje_vrednosti_svih_nodeova()
        for node_id in self.lokacije.keys():
            if node_id in poslednji_podaci:
                self.node_data[node_id] = poslednji_podaci[node_id]
                print(f"Node {node_id}: {self.node_data[node_id]}")
            else:
                print(f"Node {node_id}: Nema podataka u bazi.")

    
    def generisi_mapu(self):
        m = folium.Map(location=[44.016521, 21.005859], zoom_start=7)

        for node_id, (lat, lon) in self.lokacije.items():
            if self.node_data[node_id]:
                temp, hum, uv = self.node_data[node_id]
                istorija = poslednjih_10_vrednosti(node_id)

                istorija_html = "<div style='max-height:200px; overflow-y:auto; border:1px solid #ccc; padding:5px;'>"
                for red in istorija:
                    istorija_html += (
                    f"<b>{red['datum_vrijeme']}</b><br>"
                    f"T: {red['Temperature']}°C, H: {red['Humidity']}%, UV: {red['UV']}<br><hr>"
                )
                istorija_html += "</div>"

                popup_text = f"""
                <h3>Node {node_id}</h3>
                Temperatura: {temp}°C<br>
                Vlažnost: {hum}%<br>
                UV: {uv}<br><br>
                <b>Poslednjih 10 merenja:</b><br>
                {istorija_html}
                """
                color = "blue"
            else:
                popup_text = "<b>Nema podataka</b>"
                color = "gray"

            folium.Marker(
                location=[lat, lon],
                popup=popup_text,
                icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(m)

        data = io.BytesIO()
        m.save(data, close_file=False)
        return data.getvalue().decode()

    
    def osvezi_mapu(self, html_str):
        self.webView.setHtml(html_str)

    
    def serial_loop(self):
        try:
            ser = serial.Serial("COM6", 9600, timeout=1)
            print("Cekaju se podaci:")

            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode(errors="ignore").strip()
                    if not line:
                        continue
                    if line.lower() == "stop":
                        break

                    try:
                        delovi = line.split(",")
                        node_id = int(delovi[0])

                        if node_id in self.lokacije:
                            stari_podaci = self.node_data.get(node_id, (None, None, None))
                            temp, hum, uv = stari_podaci

                            
                            if len(delovi) == 3 and delovi[1].isalpha():
                                parametar = delovi[1].lower()
                                vrednost = delovi[2]

                                if parametar == "temp":
                                    temp = vrednost
                                    print(f"[NODE{node_id}] Promjenjena temperatura: {temp}")
                                elif parametar == "hum":
                                    hum = vrednost
                                    print(f"[NODE{node_id}] Promjenjena vlažnost: {hum}")
                                elif parametar == "uv":
                                    uv = vrednost
                                    print(f"[NODE{node_id}] Promjenjen UV: {uv}")
                                else:
                                    print(f"[NODE{node_id}] Nepoznat parametar: {parametar}")
                                    continue

                            
                            elif len(delovi) == 2:
                                temp = delovi[1]
                                print(f"[NODE{node_id}] Promjenjena temperatura: {temp}")

                            
                            elif len(delovi) == 3 and delovi[1].replace('.', '', 1).isdigit():
                                temp = delovi[1]
                                hum = delovi[2]
                                print(f"[NODE{node_id}] Promenjena temperatura i vlažnost: T={temp}°C, H={hum}%")

                            
                            elif len(delovi) == 4:
                                temp = delovi[1]
                                hum = delovi[2]
                                uv = delovi[3]
                                print(f"[NODE{node_id}] Sve promenjeno: T={temp}, H={hum}, UV={uv}")

                            else:
                                print(f"Neispravan format: {line}")
                                continue

                            
                            self.node_data[node_id] = (temp, hum, uv)
                            sacuvani_podaci(node_id, temp, hum, uv)

                           
                            html_str = self.generisi_mapu()
                            self.signali.mapa_azurirana.emit(html_str)

                    except Exception as e:
                        print(f"Greška: {e}")

                time.sleep(0.1)

        except serial.SerialException as e:
            print(f"Greška pri otvaranju COM porta: {e}")
        finally:
            if 'ser' in locals() and ser.is_open:
                ser.close()
                print("Serijski port zatvoren.")

   
    def otvori_analizu(self):
        from analiza import AnalizaProzor
        self.analiza_prozor = AnalizaProzor()
        self.analiza_prozor.show()
        self.hide()

    def closeEvent(self, event):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapaProzor()
    window.show()
    sys.exit(app.exec())