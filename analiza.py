import sys
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QDateTimeEdit, QApplication, QCalendarWidget, QDialog, QDialogButtonBox
)
from PySide6.QtCore import QDateTime, QDate
from bp import collection  

class CalendarDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Odaberite datum")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate.currentDate())
        layout.addWidget(self.calendar)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_selected_date(self):
        return self.calendar.selectedDate()

class AnalizaProzor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analiza podataka po node-u")
        self.resize(900, 700)  

       
        nav_layout = QHBoxLayout()
        dugme_mapa = QPushButton("Idi na Mapu")
        dugme_mapa.clicked.connect(self.otvori_mapu)
        nav_layout.addWidget(dugme_mapa)
        nav_layout.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(nav_layout)
        
        kontrola = QHBoxLayout()

        
        self.node_box = QComboBox()
        node_ids = sorted(list({doc["id"] for doc in collection.find()}))
        for n in node_ids:
            self.node_box.addItem(str(n))

       
        self.param_box = QComboBox()
        self.param_box.addItems(["Temperature", "Humidity", "UV"])

       
        vreme_layout = QVBoxLayout()
        
        
        od_layout = QHBoxLayout()
        od_layout.addWidget(QLabel("Od:"))
        self.od_vreme = QDateTimeEdit()
        self.od_vreme.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.od_vreme.setDisplayFormat("dd.MM.yyyy HH:mm")
        od_layout.addWidget(self.od_vreme)
        self.od_calendar_btn = QPushButton("📅")
        self.od_calendar_btn.clicked.connect(lambda: self.otvori_kalendar("od"))
        od_layout.addWidget(self.od_calendar_btn)
        vreme_layout.addLayout(od_layout)
        
        
        do_layout = QHBoxLayout()
        do_layout.addWidget(QLabel("Do:"))
        self.do_vreme = QDateTimeEdit()
        self.do_vreme.setDateTime(QDateTime.currentDateTime())
        self.do_vreme.setDisplayFormat("dd.MM.yyyy HH:mm")
        do_layout.addWidget(self.do_vreme)
        self.do_calendar_btn = QPushButton("📅")
        self.do_calendar_btn.clicked.connect(lambda: self.otvori_kalendar("do"))
        do_layout.addWidget(self.do_calendar_btn)
        vreme_layout.addLayout(do_layout)

        
        self.dugme = QPushButton("Prikaži grafikon")
        self.dugme.clicked.connect(self.prikazi_graf)

        kontrola.addWidget(QLabel("Node:"))
        kontrola.addWidget(self.node_box)
        kontrola.addWidget(QLabel("Parametar:"))
        kontrola.addWidget(self.param_box)
        kontrola.addLayout(vreme_layout)  
        kontrola.addWidget(self.dugme)

        layout.addLayout(kontrola)

        
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def otvori_kalendar(self, tip):
        dialog = CalendarDialog(self)
        if dialog.exec() == QDialog.Accepted:
            selected_date = dialog.get_selected_date()
            current_time = QDateTime.currentDateTime().time()
            
            if tip == "od":
                new_datetime = QDateTime(selected_date, current_time)
                self.od_vreme.setDateTime(new_datetime)
            else:  
                new_datetime = QDateTime(selected_date, current_time)
                self.do_vreme.setDateTime(new_datetime)

    def prikazi_graf(self):
        node_id = int(self.node_box.currentText())
        param = self.param_box.currentText()
        t1 = self.od_vreme.dateTime().toPython()
        t2 = self.do_vreme.dateTime().toPython()

        podaci = list(
            collection.find({
                "id": node_id,
                "datum_vrijeme": {"$gte": t1, "$lte": t2}
            }).sort("datum_vrijeme", 1)
        )

        if not podaci:
            self.ax.clear()
            self.ax.text(0.5, 0.5, "Nema podataka u ovom intervalu", ha='center')
            self.canvas.draw()
            return

        vremena = [p["datum_vrijeme"] for p in podaci]
        vrednosti = [p[param] for p in podaci]

        self.ax.clear()
        self.ax.plot(vremena, vrednosti, marker='o')
        self.ax.set_title(f"Node {node_id} — {param} kroz vreme")
        self.ax.set_xlabel("Vreme")
        self.ax.set_ylabel(param)
        self.ax.grid(True)
        self.figure.autofmt_xdate()
        self.canvas.draw()

    
    def otvori_mapu(self):
        from simulacija import MapaProzor
        self.mapa_prozor = MapaProzor()
        self.mapa_prozor.show()
        self.hide()

    def closeEvent(self, event):
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AnalizaProzor()
    window.show()
    sys.exit(app.exec())