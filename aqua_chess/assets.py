"""
assets.py – Embedded SVG chess pieces, QSS stylesheet, and color constants
for the "Aqua Chess" application (Beach & Ocean theme).

No external dependencies beyond the `chess` library (for piece-type constants).
"""

import chess

# ---------------------------------------------------------------------------
# 1. SVG Chess Pieces  (12 total: 6 piece types × 2 colors)
# ---------------------------------------------------------------------------
# White pieces: Pearl/Seashell Ivory fill (#FFF8E7), Gold stroke (#C9A84C)
# Black pieces: Deep Abyssal Teal fill (#1A3C40), Coral stroke (#E76F51)
# All SVGs use viewBox="0 0 45 45" and stroke-width="1.5".

_WHITE_FILL = "#FFF8E7"
_WHITE_STROKE = "#C9A84C"
_BLACK_FILL = "#1A3C40"
_BLACK_STROKE = "#E76F51"


def _svg(fill: str, stroke: str, inner: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45">'
        f'<g fill="{fill}" stroke="{stroke}" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'{inner}'
        f'</g></svg>'
    )


# ---- King ----------------------------------------------------------------
_KING_PATHS = (
    # Cross on top
    '<path d="M 22.5 11.63 L 22.5 6"/>'
    '<path d="M 20 8.5 L 25 8.5"/>'
    # Body: crown-like top, narrowing middle, wide base
    '<path d="M 22.5 11.63 C 27 11.63 32.5 14 32.5 20 '
    'C 32.5 25 27 28 27 28 L 18 28 C 18 28 12.5 25 12.5 20 '
    'C 12.5 14 18 11.63 22.5 11.63 Z"/>'
    # Belt / middle band
    '<path d="M 14 28 L 31 28" fill="none"/>'
    # Lower body
    '<path d="M 14 28 C 14 32 16 35 17 36 L 28 36 '
    'C 29 35 31 32 31 28"/>'
    # Base
    '<path d="M 11 38 L 34 38 C 34 38 33 36 28 36 '
    'L 17 36 C 12 36 11 38 11 38 Z"/>'
)

# ---- Queen ---------------------------------------------------------------
_QUEEN_PATHS = (
    # Crown prongs (5 points)
    '<circle cx="6" cy="12" r="2"/>'
    '<circle cx="14" cy="9" r="2"/>'
    '<circle cx="22.5" cy="8" r="2"/>'
    '<circle cx="31" cy="9" r="2"/>'
    '<circle cx="39" cy="12" r="2"/>'
    # Crown body connecting to prongs
    '<path d="M 9 26 C 17.5 24.5 30 24.5 36 26 '
    'L 39 14 L 31 11 L 22.5 10 L 14 11 L 6 14 Z"/>'
    # Belt band
    '<path d="M 9 26 C 9 28 10.5 30 10.5 30 L 34.5 30 '
    'C 34.5 30 36 28 36 26" fill="none"/>'
    # Lower body
    '<path d="M 10.5 30 C 10.5 33 13 36 15 36 '
    'L 30 36 C 32 36 34.5 33 34.5 30 '
    'L 10.5 30 Z"/>'
    # Base
    '<path d="M 11 38 L 34 38 C 34 38 33 36 30 36 '
    'L 15 36 C 12 36 11 38 11 38 Z"/>'
)

# ---- Rook ----------------------------------------------------------------
_ROOK_PATHS = (
    # Crenellations (battlements)
    '<path d="M 9 11 L 9 14 L 13 14 L 13 11 L 16 11 L 16 14 '
    'L 20 14 L 20 11 L 25 11 L 25 14 L 29 14 L 29 11 '
    'L 32 11 L 32 14 L 36 14 L 36 11 Z" />'
    # Tower body
    '<path d="M 9 14 L 9 30 L 36 30 L 36 14" fill="none"/>'
    '<path d="M 9 14 L 36 14 L 36 30 L 9 30 Z"/>'
    # Upper groove
    '<path d="M 12 18 L 33 18" fill="none"/>'
    # Base platform
    '<path d="M 7 36 L 38 36 L 38 30 L 7 30 Z"/>'
    # Bottom base
    '<path d="M 5 39 L 40 39 L 40 36 L 5 36 Z"/>'
)

# ---- Bishop --------------------------------------------------------------
_BISHOP_PATHS = (
    # Finial on top
    '<circle cx="22.5" cy="8" r="2.5"/>'
    # Mitre (pointed hat) body
    '<path d="M 22.5 11 C 18 11 13 16 13 23 '
    'C 13 28 17 30 17 30 L 28 30 '
    'C 28 30 32 28 32 23 C 32 16 27 11 22.5 11 Z"/>'
    # Slit in mitre
    '<path d="M 18 22 L 22.5 14 L 27 22" fill="none"/>'
    # Collar band
    '<path d="M 14 32 C 14 32 17 30 22.5 30 '
    'C 28 30 31 32 31 32 L 31 34 L 14 34 Z"/>'
    # Base
    '<path d="M 11 38 L 34 38 L 34 34 C 34 34 31 32 31 32 '
    'L 14 32 C 14 32 11 34 11 34 Z"/>'
)

# ---- Knight --------------------------------------------------------------
_KNIGHT_PATHS = (
    # Horse head profile with curved neck
    '<path d="M 22 10 C 19 6 14 7 13 9 '
    'C 11.5 10 10 12 10 12 '
    'L 8 17 C 8 17 10 16.5 11 15 '
    'C 11 17 12 19 12 19 '
    'L 11 25 C 11 27 12 30 12 30 '
    'L 33 30 C 33 30 34 27 34 25 '
    'L 34 22 C 34 18 31 14 28 12 '
    'C 26 11 24 11 22 10 Z"/>'
    # Eye
    '<circle cx="17" cy="13" r="1.2" fill="none"/>'
    # Nostril
    '<circle cx="11.5" cy="15.5" r="0.7" fill="none"/>'
    # Mane accent
    '<path d="M 22 10 C 24 12 26 13 27 14" fill="none"/>'
    # Collar
    '<path d="M 10 32 L 35 32 L 35 30 L 10 30 Z"/>'
    # Base
    '<path d="M 8 38 L 37 38 L 37 34 C 37 34 35 32 35 32 '
    'L 10 32 C 10 32 8 34 8 34 Z"/>'
)

# ---- Pawn ----------------------------------------------------------------
_PAWN_PATHS = (
    # Round head
    '<circle cx="22.5" cy="12" r="5"/>'
    # Neck / tapered column
    '<path d="M 18.5 17 C 18.5 17 19.5 22 19 25 '
    'L 26 25 C 25.5 22 26.5 17 26.5 17 Z"/>'
    # Middle flare
    '<path d="M 17 28 C 17 28 19 25 22.5 25 '
    'C 26 25 28 28 28 28 Z"/>'
    # Lower body
    '<path d="M 15 33 C 15 33 17 28 22.5 28 '
    'C 28 28 30 33 30 33 Z"/>'
    # Base
    '<path d="M 12 38 L 33 38 C 33 38 30 33 22.5 33 '
    'C 15 33 12 38 12 38 Z"/>'
)

# Assemble the mapping
_PIECE_INNER = {
    chess.KING:   _KING_PATHS,
    chess.QUEEN:  _QUEEN_PATHS,
    chess.ROOK:   _ROOK_PATHS,
    chess.BISHOP: _BISHOP_PATHS,
    chess.KNIGHT: _KNIGHT_PATHS,
    chess.PAWN:   _PAWN_PATHS,
}

PIECE_SVGS: dict[tuple[bool, int], str] = {}
for _piece_type, _inner in _PIECE_INNER.items():
    PIECE_SVGS[(chess.WHITE, _piece_type)] = _svg(_WHITE_FILL, _WHITE_STROKE, _inner)
    PIECE_SVGS[(chess.BLACK, _piece_type)] = _svg(_BLACK_FILL, _BLACK_STROKE, _inner)


# ---------------------------------------------------------------------------
# 2. QSS Stylesheet
# ---------------------------------------------------------------------------
STYLESHEET = """
/* ===== Aqua Chess – Beach & Ocean Theme ===== */

/* --- Main window gradient --- */
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #E0F7FA,
        stop:1 #006064
    );
}

/* --- Central area --- */
QWidget#centralArea {
    background: transparent;
}

/* --- Sidebar --- */
QWidget#sidebar {
    background: rgba(255, 255, 255, 0.08);
    border: none;
}

/* --- Glassmorphism Group Boxes (cards) --- */
QGroupBox {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.30);
    border-radius: 12px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #B2DFDB;
    font-size: 12px;
}

/* --- Labels --- */
QLabel {
    color: #FFFFFF;
    font-size: 13px;
    background: transparent;
}
QLabel#titleLabel {
    font-size: 22px;
    font-weight: bold;
    color: #FFFFFF;
    letter-spacing: 1px;
    padding-bottom: 2px;
}
QLabel#subtitleLabel {
    font-size: 12px;
    color: #B2DFDB;
}
QLabel#statusLabel {
    font-size: 12px;
    font-weight: bold;
    color: #E0F2F1;
    background: rgba(0, 77, 64, 0.70);
    border: 1px solid rgba(128, 222, 234, 0.35);
    border-radius: 8px;
    padding: 8px 10px;
    min-height: 22px;
}
QLabel#sectionLabel {
    font-size: 11px;
    font-weight: bold;
    color: #80DEEA;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 4px;
}
QLabel#capturedLabel {
    background: rgba(0, 40, 45, 0.50);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 13px;
    color: #E0F7FA;
    min-height: 20px;
}

/* --- Buttons (Coral Accent) --- */
QPushButton {
    background-color: #E76F51;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: bold;
    min-height: 22px;
}
QPushButton#actionBtn {
    background-color: #E76F51;
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-radius: 8px;
    padding: 7px 6px;
    font-size: 11px;
    font-weight: bold;
    min-height: 22px;
}
QPushButton#actionBtn:hover {
    background-color: #D4573D;
    border-color: rgba(255, 255, 255, 0.40);
}
QPushButton#actionBtn:pressed {
    background-color: #C04B33;
}
QPushButton:hover {
    background-color: #D4573D;
}
QPushButton:pressed {
    background-color: #C04B33;
}
QPushButton:disabled {
    background-color: rgba(231, 111, 81, 0.40);
    color: rgba(255, 255, 255, 0.50);
}

/* --- Combo Boxes --- */
QComboBox {
    background-color: #004D40;
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
    min-height: 22px;
}
QComboBox:hover {
    border: 1px solid #E76F51;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid rgba(255, 255, 255, 0.15);
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}
QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}
QComboBox QAbstractItemView {
    background-color: #004D40;
    color: #FFFFFF;
    selection-background-color: #E76F51;
    selection-color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-radius: 4px;
    outline: none;
}

/* --- Table Widget (Move History) --- */
QTableWidget {
    background-color: rgba(0, 50, 50, 0.60);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    gridline-color: rgba(255, 255, 255, 0.08);
    font-size: 12px;
    selection-background-color: rgba(231, 111, 81, 0.45);
    selection-color: #FFFFFF;
    outline: none;
}
QTableWidget::item {
    padding: 4px 6px;
}
QTableWidget::item:selected {
    background-color: rgba(231, 111, 81, 0.45);
}

QHeaderView {
    background: transparent;
}
QHeaderView::section {
    background-color: rgba(0, 77, 64, 0.80);
    color: #B2DFDB;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
    padding: 5px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* --- Scrollbar (Thin, Coral Accent) --- */
QScrollBar:vertical {
    background: rgba(0, 50, 50, 0.30);
    width: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #E76F51;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #D4573D;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
    border: none;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background: rgba(0, 50, 50, 0.30);
    height: 8px;
    margin: 0;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #E76F51;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #D4573D;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
    background: none;
    border: none;
}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

/* --- Tooltips --- */
QToolTip {
    background-color: #004D40;
    color: #FFFFFF;
    border: 1px solid #E76F51;
    border-radius: 4px;
    padding: 4px;
    font-size: 11px;
}
"""


# ---------------------------------------------------------------------------
# 3. Color Constants
# ---------------------------------------------------------------------------
COLORS: dict[str, str] = {
    'light_square':  '#F4E1C1',                 # Golden Beach Sand
    'dark_square':   '#2A9D8F',                 # Turquoise Lagoon
    'board_border':  '#8D6E63',                 # Driftwood Teak
    'last_move':     '#E76F51',                 # Coral Sunset (40% opacity)
    'legal_move':    '#A8DADC',                 # Seafoam
    'check':         '#E63946',                 # Red Coral
    'selected':      '#E9C46A',                 # Sandy Gold
    'coord_text':    '#EFEBE9',                 # Light cream
    'bg_sky':        '#E0F7FA',
    'bg_ocean':      '#006064',
    'sidebar_bg':    'rgba(255,255,255,0.08)',
    'eval_white':    '#FFF8E7',
    'eval_black':    '#1A3C40',
    'coral_accent':  '#E76F51',
}
