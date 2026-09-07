"""Application entry point: sensor map and analysis in a single window."""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from SourceCode.map_window import MapWindow
from SourceCode.analysis_window import AnalysisWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor Map & Analysis")
        self.resize(1000,800)

        self.map_page=MapWindow()
        self.analysis_page=AnalysisWindow()

        self.stack=QStackedWidget()
        self.stack.addWidget(self.map_page)
        self.stack.addWidget(self.analysis_page)
        self.setCentralWidget(self.stack)

        self.map_page.show_analysis.connect(lambda: self.stack.setCurrentWidget(self.analysis_page))
        self.analysis_page.show_map.connect(lambda: self.stack.setCurrentWidget(self.map_page))

    def closeEvent(self,event):
        self.map_page.stop()
        super().closeEvent(event)

def main():
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
        main()