"""
Aqua Chess — Main GUI Module
Beach & Ocean themed chess interface built with PySide6.
"""

import copy
import chess

from PySide6.QtCore import Qt, Signal, QSize, QByteArray, QRectF, QPointF, QThread
from PySide6.QtGui import (
    QPainter, QColor, QFont, QLinearGradient, QPen, QBrush, QIcon,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QTableWidget, QTableWidgetItem, QDialog,
    QSizePolicy, QHeaderView, QAbstractItemView,
)
from PySide6.QtSvg import QSvgRenderer

from engine import AquaEngine
from assets import PIECE_SVGS, STYLESHEET, COLORS


# ---------------------------------------------------------------------------
# Unicode piece symbols for captured-pieces display
# ---------------------------------------------------------------------------
UNICODE_PIECES = {
    (chess.WHITE, chess.PAWN): "♙",
    (chess.WHITE, chess.KNIGHT): "♘",
    (chess.WHITE, chess.BISHOP): "♗",
    (chess.WHITE, chess.ROOK): "♖",
    (chess.WHITE, chess.QUEEN): "♕",
    (chess.WHITE, chess.KING): "♔",
    (chess.BLACK, chess.PAWN): "♟",
    (chess.BLACK, chess.KNIGHT): "♞",
    (chess.BLACK, chess.BISHOP): "♝",
    (chess.BLACK, chess.ROOK): "♜",
    (chess.BLACK, chess.QUEEN): "♛",
    (chess.BLACK, chess.KING): "♚",
}

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

INITIAL_MATERIAL = {
    chess.PAWN: 8,
    chess.KNIGHT: 2,
    chess.BISHOP: 2,
    chess.ROOK: 2,
    chess.QUEEN: 1,
    chess.KING: 1,
}

DIFFICULTY_MAP = {
    "🌴 Beach Breeze": "Beach Breeze",
    "🌊 High Tide": "High Tide",
    "🌊 Tsunami": "Tsunami",
}


# ═══════════════════════════════════════════════════════════════════════════
# AIWorker — background thread for engine search
# ═══════════════════════════════════════════════════════════════════════════
class AIWorker(QThread):
    """Run the engine search off the GUI thread."""

    result_ready = Signal(object, int)

    def __init__(self, board: chess.Board, difficulty: str, engine: AquaEngine, parent=None):
        super().__init__(parent)
        self.board = board  # already a deep copy
        self.difficulty = difficulty
        self.engine = engine

    def run(self):
        best_move, eval_score = self.engine.find_best_move(self.board, self.difficulty)
        self.result_ready.emit(best_move, eval_score)


# ═══════════════════════════════════════════════════════════════════════════
# PromotionDialog — pick a promotion piece
# ═══════════════════════════════════════════════════════════════════════════
class PromotionDialog(QDialog):
    """Beach cabana–style popup for pawn promotion."""

    def __init__(self, color: chess.Color, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🐚 Promotion")
        self.setModal(True)
        self.chosen_piece = chess.QUEEN  # default

        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        for piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
            btn = QPushButton()
            btn.setFixedSize(64, 64)
            btn.setStyleSheet(
                "QPushButton {"
                "  background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
                "    stop:0 #E0F7FA, stop:1 #B2EBF2);"
                "  border: 2px solid #00838F;"
                "  border-radius: 8px;"
                "}"
                "QPushButton:hover { background: #B2EBF2; }"
            )
            svg_key = (color, piece_type)
            svg_data = PIECE_SVGS.get(svg_key, "")
            if svg_data:
                renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
                from PySide6.QtGui import QPixmap
                pixmap = QPixmap(56, 56)
                pixmap.fill(QColor(0, 0, 0, 0))
                p = QPainter(pixmap)
                renderer.render(p)
                p.end()
                btn.setIcon(QIcon(pixmap))
                btn.setIconSize(QSize(52, 52))

            # Bind the piece type to the button click
            btn.clicked.connect(self._make_handler(piece_type))
            layout.addWidget(btn)

        self.setStyleSheet(
            "QDialog {"
            "  background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            "    stop:0 #E0F7FA, stop:1 #FFF8E1);"
            "  border-radius: 12px;"
            "}"
        )

    def _make_handler(self, piece_type):
        def handler():
            self.chosen_piece = piece_type
            self.accept()
        return handler


# ═══════════════════════════════════════════════════════════════════════════
# EvalBar — vertical evaluation indicator
# ═══════════════════════════════════════════════════════════════════════════
class EvalBar(QWidget):
    """Vertical bar showing the engine evaluation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.eval_score = 0  # centipawns, positive = white advantage
        self.setFixedWidth(30)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

    def set_eval(self, score_cp: int):
        """Update the evaluation. *score_cp* is in centipawns from White's perspective."""
        self.eval_score = score_cp
        self.update()

    # Sigmoid-like mapping: ±500cp ≈ 80 % fill
    @staticmethod
    def _score_to_ratio(cp: int) -> float:
        """Return 0..1 where 0.5 = equal, 1.0 = white winning fully."""
        import math
        # k chosen so that sigmoid(500*k)≈0.8  =>  k ≈ ln(4)/500 ≈ 0.00277
        k = 0.00277
        return 1.0 / (1.0 + math.exp(-k * cp))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Rounded clip for modern glass tide gauge look
        clip_path = QPainterPath()
        clip_path.addRoundedRect(0, 0, w, h, 8, 8)
        painter.setClipPath(clip_path)

        # Determine if the score is a mate score (very large absolute value)
        is_mate = abs(self.eval_score) > 90000
        if is_mate:
            mate_in = abs(self.eval_score) - 100000
            if self.eval_score > 0:
                white_ratio = 1.0
            else:
                white_ratio = 0.0
        else:
            white_ratio = self._score_to_ratio(self.eval_score)

        # Black region (top)
        black_h = int(h * (1.0 - white_ratio))
        black_grad = QLinearGradient(0, 0, 0, black_h)
        black_grad.setColorAt(0.0, QColor("#1A3C40"))
        black_grad.setColorAt(1.0, QColor("#2E5D62"))
        painter.setBrush(QBrush(black_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, black_h)

        # White region (bottom)
        white_grad = QLinearGradient(0, black_h, 0, h)
        white_grad.setColorAt(0.0, QColor("#F5F0E1"))
        white_grad.setColorAt(1.0, QColor("#FFF8E7"))
        painter.setBrush(QBrush(white_grad))
        painter.drawRect(0, black_h, w, h - black_h)

        # Divider line
        painter.setPen(QPen(QColor("#00838F"), 1.5))
        painter.drawLine(0, black_h, w, black_h)

        # Eval text
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)

        if is_mate:
            mate_moves = abs(abs(self.eval_score) - 100000)
            text = f"M{mate_moves}" if self.eval_score > 0 else f"-M{mate_moves}"
        else:
            pawns = self.eval_score / 100.0
            text = f"{pawns:+.1f}"

        # Draw text in the region that has more space
        if white_ratio >= 0.5:
            # Draw in white region
            painter.setPen(QColor("#1A3C40"))
            text_rect = QRectF(0, max(black_h, h - 28), w, 24)
        else:
            # Draw in black region
            painter.setPen(QColor("#FFF8E7"))
            text_rect = QRectF(0, min(black_h - 24, 4), w, 24)

        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

        # Outer glass border
        painter.setClipping(False)
        painter.setPen(QPen(QColor(255, 255, 255, 70), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.75, 0.75, w - 1.5, h - 1.5), 8, 8)

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════
# ChessBoard — interactive board widget
# ═══════════════════════════════════════════════════════════════════════════
class ChessBoard(QWidget):
    """Interactive chess board drawn with QPainter."""

    move_made = Signal(object)

    BORDER = 30  # px for coordinate border

    def __init__(self, board: chess.Board, parent=None):
        super().__init__(parent)
        self.board = board
        self.flipped = False
        self.selected_square: int | None = None
        self.legal_moves_for_selected: list[chess.Move] = []
        self.last_move: chess.Move | None = None
        self.interactive = True
        self.player_color: chess.Color = chess.WHITE
        self.setMinimumSize(480, 480)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def sizeHint(self) -> QSize:
        return QSize(600, 600)

    # ----- coordinate helpers -----
    def _square_size(self) -> float:
        usable = max(80.0, min(self.width(), self.height()) - 2 * self.BORDER)
        return usable / 8.0

    def _square_rect(self, sq: int) -> QRectF:
        ss = self._square_size()
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        if self.flipped:
            col = 7 - file
            row = rank
        else:
            col = file
            row = 7 - rank
        x = self.BORDER + col * ss
        y = self.BORDER + row * ss
        return QRectF(x, y, ss, ss)

    def _pos_to_square(self, pos) -> int | None:
        ss = self._square_size()
        x = pos.x() - self.BORDER
        y = pos.y() - self.BORDER
        if x < 0 or y < 0:
            return None
        col = int(x / ss)
        row = int(y / ss)
        if col < 0 or col > 7 or row < 0 or row > 7:
            return None
        if self.flipped:
            file = 7 - col
            rank = row
        else:
            file = col
            rank = 7 - row
        return chess.square(file, rank)

    # ----- painting -----
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        ss = self._square_size()
        board_px = ss * 8

        # ---- border ----
        border_color = QColor(COLORS["board_border"])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(border_color))
        painter.drawRect(QRectF(0, 0, board_px + 2 * self.BORDER, board_px + 2 * self.BORDER))

        # ---- coordinate labels ----
        coord_color = QColor(COLORS["coord_text"])
        coord_font = QFont("Segoe UI", max(8, int(ss * 0.22)), QFont.Weight.Bold)
        painter.setFont(coord_font)
        painter.setPen(coord_color)

        for i in range(8):
            # File labels (a–h) along bottom
            file_idx = (7 - i) if self.flipped else i
            file_label = chr(ord("a") + file_idx)
            x = self.BORDER + i * ss + ss / 2
            painter.drawText(
                QRectF(x - 10, self.BORDER + board_px + 2, 20, self.BORDER - 4),
                Qt.AlignmentFlag.AlignCenter,
                file_label,
            )
            # Also along top
            painter.drawText(
                QRectF(x - 10, 2, 20, self.BORDER - 4),
                Qt.AlignmentFlag.AlignCenter,
                file_label,
            )

            # Rank labels (1–8) along left
            rank_idx = i if self.flipped else (7 - i)
            rank_label = str(rank_idx + 1)
            y = self.BORDER + i * ss + ss / 2
            painter.drawText(
                QRectF(2, y - 10, self.BORDER - 4, 20),
                Qt.AlignmentFlag.AlignCenter,
                rank_label,
            )
            # Also along right
            painter.drawText(
                QRectF(self.BORDER + board_px + 2, y - 10, self.BORDER - 4, 20),
                Qt.AlignmentFlag.AlignCenter,
                rank_label,
            )

        # ---- squares ----
        light = QColor(COLORS["light_square"])
        dark = QColor(COLORS["dark_square"])

        for sq in chess.SQUARES:
            rect = self._square_rect(sq)
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)
            is_light = (file + rank) % 2 == 1
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(light if is_light else dark))
            painter.drawRect(rect)

        # ---- last move highlight ----
        if self.last_move is not None:
            lm_color = QColor(COLORS["last_move"])
            lm_color.setAlpha(90)
            painter.setBrush(QBrush(lm_color))
            painter.setPen(Qt.PenStyle.NoPen)
            for sq in (self.last_move.from_square, self.last_move.to_square):
                painter.drawRect(self._square_rect(sq))

        # ---- selected square highlight ----
        if self.selected_square is not None:
            sel_color = QColor(COLORS["selected"])
            sel_color.setAlpha(120)
            painter.setBrush(QBrush(sel_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self._square_rect(self.selected_square))

        # ---- check highlight ----
        if self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                kr = self._square_rect(king_sq)
                center = kr.center()
                radius = ss * 0.48
                check_grad = QLinearGradient(
                    center.x() - radius, center.y() - radius,
                    center.x() + radius, center.y() + radius,
                )
                check_grad.setColorAt(0.0, QColor(255, 60, 60, 130))
                check_grad.setColorAt(0.5, QColor(255, 30, 30, 80))
                check_grad.setColorAt(1.0, QColor(255, 60, 60, 130))
                painter.setBrush(QBrush(check_grad))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(center, radius, radius)

        # ---- pieces ----
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece is None:
                continue
            svg_key = (piece.color, piece.piece_type)
            svg_data = PIECE_SVGS.get(svg_key)
            if svg_data is None:
                continue
            renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
            rect = self._square_rect(sq)
            # Slight padding so pieces don't touch the edges
            padding = ss * 0.06
            piece_rect = rect.adjusted(padding, padding, -padding, -padding)
            renderer.render(painter, piece_rect)

        # ---- legal move indicators ----
        if self.selected_square is not None:
            seafoam = QColor("#66CDAA")
            seafoam.setAlpha(190)
            for move in self.legal_moves_for_selected:
                target_rect = self._square_rect(move.to_square)
                center = target_rect.center()
                target_piece = self.board.piece_at(move.to_square)
                if target_piece is not None:
                    # Capture indicator: prominent coral target ring around piece
                    painter.setPen(QPen(QColor("#E76F51"), max(2.5, ss * 0.08)))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(center, ss * 0.42, ss * 0.42)
                else:
                    # Empty square: small seafoam filled circle
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(seafoam))
                    painter.drawEllipse(center, ss * 0.16, ss * 0.16)

        painter.end()

    # ----- interaction -----
    def mousePressEvent(self, event):
        if not self.interactive:
            return
        if self.board.turn != self.player_color:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        sq = self._pos_to_square(event.position())
        if sq is None:
            return

        # If a piece is already selected, try to make a move
        if self.selected_square is not None:
            # Check if the target is a legal destination
            matching_moves = [
                m for m in self.legal_moves_for_selected if m.to_square == sq
            ]
            if matching_moves:
                move = matching_moves[0]
                # Check for pawn promotion
                piece = self.board.piece_at(self.selected_square)
                if (
                    piece is not None
                    and piece.piece_type == chess.PAWN
                    and chess.square_rank(sq) in (0, 7)
                ):
                    dlg = PromotionDialog(piece.color, parent=self)
                    if dlg.exec() == QDialog.DialogCode.Accepted:
                        promo_piece = dlg.chosen_piece
                        promo_moves = [
                            m for m in matching_moves if m.promotion == promo_piece
                        ]
                        move = promo_moves[0] if promo_moves else matching_moves[0]
                    else:
                        # Cancelled promotion
                        self.selected_square = None
                        self.legal_moves_for_selected = []
                        self.update()
                        return

                self.selected_square = None
                self.legal_moves_for_selected = []
                self.move_made.emit(move)
                self.update()
                return

            # Clicked same square → deselect
            if sq == self.selected_square:
                self.selected_square = None
                self.legal_moves_for_selected = []
                self.update()
                return

            # Clicked another own piece → reselect
            piece_at_sq = self.board.piece_at(sq)
            if piece_at_sq is not None and piece_at_sq.color == self.board.turn and piece_at_sq.color == self.player_color:
                self._select_square(sq)
                return

            # Clicked empty non-legal square → deselect
            self.selected_square = None
            self.legal_moves_for_selected = []
            self.update()
            return

        # No piece selected yet — try to select
        piece = self.board.piece_at(sq)
        if piece is not None and piece.color == self.board.turn and piece.color == self.player_color:
            self._select_square(sq)

    def _select_square(self, sq: int):
        self.selected_square = sq
        self.legal_moves_for_selected = [
            m for m in self.board.legal_moves if m.from_square == sq
        ]
        self.update()


# ═══════════════════════════════════════════════════════════════════════════
# CentralBackground — paints coastal gradient behind everything
# ═══════════════════════════════════════════════════════════════════════════
class CentralBackground(QWidget):
    """Central widget that paints a coastal gradient background."""

    def paintEvent(self, event):
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#0D3B66"))   # deep ocean
        grad.setColorAt(0.35, QColor("#1B6B7D"))  # mid-sea
        grad.setColorAt(0.7, QColor("#5AB0B2"))   # shallows
        grad.setColorAt(1.0, QColor("#C8E6C9"))   # sandy shore
        painter.fillRect(self.rect(), grad)
        painter.end()


# ═══════════════════════════════════════════════════════════════════════════
# AquaChessWindow — main application window
# ═══════════════════════════════════════════════════════════════════════════
class AquaChessWindow(QMainWindow):
    """Top-level window for Aqua Chess."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aqua Chess 🌊")
        self.setMinimumSize(900, 650)

        # --- core state ---
        self.board = chess.Board()
        self.engine = AquaEngine()
        self.player_color: chess.Color = chess.WHITE
        self.ai_worker: AIWorker | None = None
        self.last_eval: int = 0

        # --- stylesheet ---
        self.setStyleSheet(STYLESHEET)

        # --- central widget with gradient ---
        central = CentralBackground()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ---- eval bar (left) ----
        self.eval_bar = EvalBar()
        main_layout.addWidget(self.eval_bar)

        # ---- chess board (center) ----
        self.chess_board = ChessBoard(self.board)
        self.chess_board.move_made.connect(self.on_player_move)
        main_layout.addWidget(self.chess_board, stretch=1)

        # ---- sidebar (right) ----
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 12)
        sidebar_layout.setSpacing(10)

        # Title
        title_label = QLabel("🌊 Aqua Chess")
        title_label.setObjectName("titleLabel")
        title_font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title_label)

        # Status
        self.status_label = QLabel("Your Turn — White to Move")
        self.status_label.setObjectName("statusLabel")
        status_font = QFont("Segoe UI", 11)
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        sidebar_layout.addWidget(self.status_label)

        # Difficulty selector
        diff_label = QLabel("Difficulty")
        diff_label.setObjectName("sectionLabel")
        sidebar_layout.addWidget(diff_label)
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["🌴 Beach Breeze", "🌊 High Tide", "🌊 Tsunami"])
        self.difficulty_combo.setObjectName("difficultyCombo")
        sidebar_layout.addWidget(self.difficulty_combo)

        # Color selector
        color_label = QLabel("Play As")
        color_label.setObjectName("sectionLabel")
        sidebar_layout.addWidget(color_label)
        self.color_combo = QComboBox()
        self.color_combo.addItems(["⬜ Play as White", "⬛ Play as Black"])
        self.color_combo.setObjectName("colorCombo")
        self.color_combo.currentIndexChanged.connect(self._on_color_changed)
        sidebar_layout.addWidget(self.color_combo)

        # Captured pieces
        cap_label = QLabel("Captured Pieces")
        cap_label.setObjectName("sectionLabel")
        sidebar_layout.addWidget(cap_label)

        self.captured_white_label = QLabel("")  # pieces captured BY white (black pieces)
        self.captured_white_label.setObjectName("capturedLabel")
        self.captured_white_label.setFont(QFont("Segoe UI", 12))
        sidebar_layout.addWidget(self.captured_white_label)

        self.captured_black_label = QLabel("")  # pieces captured BY black (white pieces)
        self.captured_black_label.setObjectName("capturedLabel")
        self.captured_black_label.setFont(QFont("Segoe UI", 12))
        sidebar_layout.addWidget(self.captured_black_label)

        # Move history table
        hist_label = QLabel("Move History")
        hist_label.setObjectName("sectionLabel")
        sidebar_layout.addWidget(hist_label)

        self.move_table = QTableWidget(0, 3)
        self.move_table.setHorizontalHeaderLabels(["#", "White", "Black"])
        self.move_table.setObjectName("moveTable")
        self.move_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.move_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.move_table.verticalHeader().setVisible(False)
        header = self.move_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        sidebar_layout.addWidget(self.move_table, stretch=1)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.new_game_btn = QPushButton("🆕 New Game")
        self.new_game_btn.setObjectName("actionBtn")
        self.new_game_btn.clicked.connect(self.new_game)
        btn_layout.addWidget(self.new_game_btn)

        self.undo_btn = QPushButton("↩️ Undo Move")
        self.undo_btn.setObjectName("actionBtn")
        self.undo_btn.clicked.connect(self.undo_move)
        btn_layout.addWidget(self.undo_btn)

        self.flip_btn = QPushButton("🔄 Flip Board")
        self.flip_btn.setObjectName("actionBtn")
        self.flip_btn.clicked.connect(self.flip_board)
        btn_layout.addWidget(self.flip_btn)

        sidebar_layout.addLayout(btn_layout)

        main_layout.addWidget(sidebar)

        # --- initial display ---
        self.update_display()

    # ------------------------------------------------------------------
    # Color change
    # ------------------------------------------------------------------
    def _on_color_changed(self, index: int):
        self.player_color = chess.WHITE if index == 0 else chess.BLACK
        self.chess_board.player_color = self.player_color
        self.new_game()

    # ------------------------------------------------------------------
    # Game actions
    # ------------------------------------------------------------------
    def on_player_move(self, move: chess.Move):
        """Called when the human makes a move on the board."""
        self.board.push(move)
        self.chess_board.last_move = move
        self.chess_board.selected_square = None
        self.chess_board.legal_moves_for_selected = []
        self.update_display()

        if self.check_game_over():
            self.chess_board.interactive = False
            return

        self.trigger_ai_move()

    def trigger_ai_move(self):
        """Start the AI search in a background thread."""
        if self.board.turn == self.player_color:
            self.chess_board.interactive = True
            return
        if self.board.is_game_over():
            self.chess_board.interactive = False
            return

        self.chess_board.interactive = False
        self.status_label.setText("AI is thinking in the waves... 🌊")

        difficulty_key = self.difficulty_combo.currentText()
        difficulty = DIFFICULTY_MAP.get(difficulty_key, "Beach Breeze")

        board_copy = copy.deepcopy(self.board)
        self.ai_worker = AIWorker(board_copy, difficulty, self.engine, parent=self)
        self.ai_worker.result_ready.connect(self.on_ai_move_ready)
        self.ai_worker.start()

    def on_ai_move_ready(self, move: chess.Move, eval_score: int):
        """Handle the AI's chosen move."""
        if move is not None and move in self.board.legal_moves:
            self.board.push(move)
            self.chess_board.last_move = move
            self.last_eval = eval_score
            self.eval_bar.set_eval(eval_score)
        self.ai_worker = None
        self.chess_board.interactive = not self.board.is_game_over()
        self.update_display()
        self.check_game_over()

    def new_game(self):
        """Reset everything for a fresh game."""
        if self.ai_worker is not None and self.ai_worker.isRunning():
            self.ai_worker.terminate()
            self.ai_worker.wait(500)
            self.ai_worker = None

        self.board.reset()
        self.engine.reset()
        self.chess_board.board = self.board
        self.chess_board.player_color = self.player_color
        self.chess_board.last_move = None
        self.chess_board.selected_square = None
        self.chess_board.legal_moves_for_selected = []
        self.last_eval = 0
        self.eval_bar.set_eval(0)
        self.chess_board.interactive = (self.player_color == chess.WHITE)
        self.update_display()

        # If the player chose Black, AI moves first
        if self.player_color == chess.BLACK:
            self.chess_board.flipped = True
            self.trigger_ai_move()
        else:
            self.chess_board.flipped = False

    def undo_move(self):
        """Undo moves back to the player's turn."""
        if self.ai_worker is not None and self.ai_worker.isRunning():
            return  # don't undo while AI is thinking

        if not self.board.move_stack:
            return

        # If it's the AI's turn (e.g. human just moved, game over or AI didn't run), pop 1 move
        if self.board.turn != self.player_color:
            self.board.pop()
        else:
            # It's player's turn: pop AI move then player move
            if len(self.board.move_stack) >= 2:
                self.board.pop()  # AI move
                self.board.pop()  # player move
            elif len(self.board.move_stack) == 1 and self.player_color == chess.WHITE:
                self.board.pop()
            else:
                return

        # Update last move highlight
        if self.board.move_stack:
            self.chess_board.last_move = self.board.peek()
        else:
            self.chess_board.last_move = None

        self.chess_board.selected_square = None
        self.chess_board.legal_moves_for_selected = []
        self.chess_board.interactive = True
        self.update_display()

    def flip_board(self):
        """Toggle board orientation."""
        self.chess_board.flipped = not self.chess_board.flipped
        self.chess_board.update()

    # ------------------------------------------------------------------
    # Display updates
    # ------------------------------------------------------------------
    def update_display(self):
        """Refresh all UI elements to match current board state."""
        self.chess_board.update()
        self.update_move_history()
        self.update_captured_pieces()
        self._update_status()
        if self.ai_worker is None or not self.ai_worker.isRunning():
            self.eval_bar.set_eval(self.engine.evaluate(self.board))

    def _update_status(self):
        """Set the status label based on current game state."""
        if self.board.is_game_over():
            return  # status was already set by check_game_over

        if self.board.turn == self.player_color:
            color_name = "White" if self.board.turn == chess.WHITE else "Black"
            self.status_label.setText(f"Your Turn — {color_name} to Move")
        else:
            self.status_label.setText("AI is thinking in the waves... 🌊")

    def update_move_history(self):
        """Parse board.move_stack into SAN pairs and fill the table."""
        # We need to replay moves on a temporary board to get correct SAN
        temp_board = chess.Board()
        san_moves: list[str] = []
        for move in self.board.move_stack:
            san = temp_board.san(move)
            san_moves.append(san)
            temp_board.push(move)

        num_rows = (len(san_moves) + 1) // 2
        self.move_table.setRowCount(num_rows)

        for i in range(num_rows):
            # Move number
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.move_table.setItem(i, 0, num_item)

            # White move
            white_idx = i * 2
            if white_idx < len(san_moves):
                w_item = QTableWidgetItem(san_moves[white_idx])
                w_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.move_table.setItem(i, 1, w_item)
            else:
                self.move_table.setItem(i, 1, QTableWidgetItem(""))

            # Black move
            black_idx = i * 2 + 1
            if black_idx < len(san_moves):
                b_item = QTableWidgetItem(san_moves[black_idx])
                b_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.move_table.setItem(i, 2, b_item)
            else:
                self.move_table.setItem(i, 2, QTableWidgetItem(""))

        # Scroll to the bottom
        if num_rows > 0:
            self.move_table.scrollToBottom()

    def update_captured_pieces(self):
        """Compute captured pieces by comparing initial material to current board."""
        # Count current pieces on the board for each color
        white_counts: dict[int, int] = {}
        black_counts: dict[int, int] = {}
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece is None:
                continue
            if piece.color == chess.WHITE:
                white_counts[piece.piece_type] = white_counts.get(piece.piece_type, 0) + 1
            else:
                black_counts[piece.piece_type] = black_counts.get(piece.piece_type, 0) + 1

        # Captured = initial - current  (captured pieces are those of the opponent)
        # "Captured BY white" means black pieces that are gone
        captured_by_white_text = ""
        captured_by_white_value = 0
        for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
            initial = INITIAL_MATERIAL.get(pt, 0)
            current = black_counts.get(pt, 0)
            diff = initial - current
            if diff > 0:
                symbol = UNICODE_PIECES.get((chess.BLACK, pt), "?")
                captured_by_white_text += symbol * diff
                captured_by_white_value += diff * PIECE_VALUES.get(pt, 0)

        captured_by_black_text = ""
        captured_by_black_value = 0
        for pt in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
            initial = INITIAL_MATERIAL.get(pt, 0)
            current = white_counts.get(pt, 0)
            diff = initial - current
            if diff > 0:
                symbol = UNICODE_PIECES.get((chess.WHITE, pt), "?")
                captured_by_black_text += symbol * diff
                captured_by_black_value += diff * PIECE_VALUES.get(pt, 0)

        # Material advantage
        advantage = captured_by_white_value - captured_by_black_value

        white_display = captured_by_white_text
        if advantage > 0:
            white_display += f" +{advantage}"

        black_display = captured_by_black_text
        if advantage < 0:
            black_display += f" +{-advantage}"

        self.captured_white_label.setText(f"⬜ {white_display}" if white_display else "⬜ —")
        self.captured_black_label.setText(f"⬛ {black_display}" if black_display else "⬛ —")

    def check_game_over(self) -> bool:
        """Check board.outcome() and display result. Returns True if game is over."""
        outcome = self.board.outcome()
        if outcome is None:
            return False

        if outcome.termination == chess.Termination.CHECKMATE:
            winner = "White" if outcome.winner == chess.WHITE else "Black"
            self.status_label.setText(f"♚ Checkmate! {winner} wins!")
        elif outcome.termination == chess.Termination.STALEMATE:
            self.status_label.setText("Draw — Stalemate")
        elif outcome.termination == chess.Termination.INSUFFICIENT_MATERIAL:
            self.status_label.setText("Draw — Insufficient Material")
        elif outcome.termination == chess.Termination.THREEFOLD_REPETITION:
            self.status_label.setText("Draw — Threefold Repetition")
        elif outcome.termination == chess.Termination.FIFTY_MOVES:
            self.status_label.setText("Draw — Fifty-Move Rule")
        else:
            self.status_label.setText("Game Over — Draw")

        return True
