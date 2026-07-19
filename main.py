# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from Backend import Backend


if __name__ == "__main__":
    QQuickStyle.setStyle("Material")
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)
    engine.addImportPath(Path(__file__).parent)
    engine.loadFromModule("AnomalibTrainer", "Main")
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())
