"""
Módulo App - Ponto de entrada da aplicação GUI.
"""

import sys
from PyQt6.QtWidgets import QApplication
from .main_window import MainWindow


def run_app():
    """Inicia a aplicação GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("PEF Analyzer")
    app.setApplicationDisplayName("PEF Analyzer")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
