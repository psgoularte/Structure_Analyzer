"""
Módulo App - Ponto de entrada da aplicação GUI.
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from .main_window import MainWindow


def run_app():
    """Inicia a aplicação GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("PEF Analyzer")
    app.setApplicationDisplayName("PEF Analyzer")
    
    # Load the stylesheet for enhanced interface (path resolved relative to this file)
    style_path = Path(__file__).resolve().parent / "resources" / "styles.qss"
    if style_path.exists():
        with open(style_path, "r", encoding="utf-8") as style_file:
            app.setStyleSheet(style_file.read())
    else:
        print(f"Aviso: stylesheet não encontrada em: {style_path}")

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
