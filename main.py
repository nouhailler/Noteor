#!/usr/bin/env python3
"""Point d'entrée de l'application Noteor."""

import sys
from pathlib import Path

# Ajoute le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

import config


def main():
    # Création des dossiers de données
    for directory in (
        config.DATA_DIR,
        config.AUDIO_DIR,
        config.IMAGE_DIR,
        config.THUMB_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    # PyQt6 doit être importé après la configuration du path
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setOrganizationName("Noteor")
    app.setStyle("Fusion")

    from ui.styles import STYLESHEET
    app.setStyleSheet(STYLESHEET)

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
