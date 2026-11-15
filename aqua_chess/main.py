"""
Aqua Chess — Main Entry Point
A beach-themed Human vs. AI chess application.
"""

import sys
import os

# High-DPI scaling configuration (must be set before QApplication)
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui import AquaChessWindow


def main():
    """Initialize and launch Aqua Chess."""
    app = QApplication(sys.argv)

    # Enable high-DPI pixmap support
    app.setStyle("Fusion")

    # Set default application font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(font)

    # Create main window
    window = AquaChessWindow()

    # Set window icon (Pearl & Gold Seashell King)
    from assets import PIECE_SVGS
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor
    from PySide6.QtCore import QByteArray
    import chess
    svg_data = PIECE_SVGS.get((chess.WHITE, chess.KING), "")
    if svg_data:
        renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        p = QPainter(pixmap)
        renderer.render(p)
        p.end()
        icon = QIcon(pixmap)
        app.setWindowIcon(icon)
        window.setWindowIcon(icon)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
