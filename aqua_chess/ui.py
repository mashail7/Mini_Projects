"""
Aqua Chess — Main GUI Module
Beach & Ocean Resort themed chess interface built with PySide6.

Features an immersive coastal panorama background, 3D driftwood & brass
chessboard, textured lagoon/sand squares, and glassmorphism sidebar.
"""

import copy
import math
import chess

from PySide6.QtCore import (
    Qt, Signal, QSize, QByteArray, QRectF, QPointF, QThread,
    QVariantAnimation, QEasingCurve, QTimer,
)
from PySide6.QtGui import (
    QPainter, QColor, QFont, QLinearGradient, QRadialGradient, QPen, QBrush,
    QIcon, QPainterPath, QConicalGradient,
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

# ---------------------------------------------------------------------------
# Timing and Animation Constants
# ---------------------------------------------------------------------------
MOVE_ANIM_DURATION_MS = 300       # Piece slide animation duration (250-350 ms)
AI_PRE_MOVE_DELAY_MS = 800        # Presentation delay before AI starts moving (700-1000 ms)
AI_POST_MOVE_PAUSE_MS = 400       # Visual pause after AI move finishes before player's turn (300-500 ms)


# ---------------------------------------------------------------------------
# PieceRendererCache — pre-loaded cache of QSvgRenderer for all 12 piece types
# ---------------------------------------------------------------------------
class PieceRendererCache:
    """Lazily-cached QSvgRenderer instances for all 12 piece types to enable smooth 60 FPS animation."""
    _renderers: dict[tuple[chess.Color, chess.PieceType], QSvgRenderer] = {}

    @classmethod
    def get(cls, color: chess.Color, piece_type: chess.PieceType) -> QSvgRenderer | None:
        key = (color, piece_type)
        if key not in cls._renderers:
            svg_data = PIECE_SVGS.get(key)
            if svg_data:
                cls._renderers[key] = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
        return cls._renderers.get(key)


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
                "    stop:0 rgba(10,38,54,0.85), stop:1 rgba(7,26,36,0.95));"
                "  border: 2px solid rgba(128,255,219,0.45);"
                "  border-radius: 10px;"
                "}"
                "QPushButton:hover {"
                "  background: rgba(42,157,143,0.55);"
                "  border-color: #E76F51;"
                "}"
            )
            renderer = PieceRendererCache.get(color, piece_type)
            if renderer:
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
            "    stop:0 rgba(10,38,54,0.92), stop:1 rgba(7,26,36,0.97));"
            "  border: 1px solid rgba(128,255,219,0.35);"
            "  border-radius: 14px;"
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
        # k chosen so that sigmoid(500*k)≈0.8  => k ≈ ln(4)/500 ≈ 0.00277
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
            if self.eval_score > 0:
                white_ratio = 1.0
            else:
                white_ratio = 0.0
        else:
            white_ratio = self._score_to_ratio(self.eval_score)

        # Black region (top)
        black_h = int(h * (1.0 - white_ratio))
        black_grad = QLinearGradient(0, 0, 0, black_h)
        black_grad.setColorAt(0.0, QColor("#071A24"))
        black_grad.setColorAt(1.0, QColor("#133B4E"))
        painter.setBrush(QBrush(black_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, black_h)

        # White region (bottom)
        white_grad = QLinearGradient(0, black_h, 0, h)
        white_grad.setColorAt(0.0, QColor("#F3E5AB"))
        white_grad.setColorAt(1.0, QColor("#FFFDF9"))
        painter.setBrush(QBrush(white_grad))
        painter.drawRect(0, black_h, w, h - black_h)

        # Divider line
        painter.setPen(QPen(QColor("#D4AF37"), 1.5))
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
            painter.setPen(QColor("#071A24"))
            text_rect = QRectF(0, max(black_h, h - 28), w, 24)
        else:
            # Draw in black region
            painter.setPen(QColor("#FFFDF9"))
            text_rect = QRectF(0, min(black_h - 24, 4), w, 24)

        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

        # Outer glass border
        painter.setClipping(False)
        painter.setPen(QPen(QColor(128, 255, 219, 70), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.75, 0.75, w - 1.5, h - 1.5), 8, 8)

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════
# ChessBoard — interactive board widget with 3D driftwood frame
# ═══════════════════════════════════════════════════════════════════════════
class ChessBoard(QWidget):
    """Interactive chess board drawn with QPainter with smooth piece slide animations."""

    move_made = Signal(object)

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

        # Movement animation state
        self.is_animating = False
        self.anim_progress = 0.0
        self.anim_moving_pieces: list[tuple[chess.Piece, int, int]] = []
        self.anim_target_squares: set[int] = set()
        self.anim_captured_info: tuple[chess.Piece, int] | None = None
        self._anim_on_finished = None

        self.move_anim = QVariantAnimation(self)
        self.move_anim.setDuration(MOVE_ANIM_DURATION_MS)
        self.move_anim.setStartValue(0.0)
        self.move_anim.setEndValue(1.0)
        self.move_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.move_anim.valueChanged.connect(self._on_anim_value_changed)
        self.move_anim.finished.connect(self._on_anim_finished)

    def sizeHint(self) -> QSize:
        return QSize(600, 600)

    def _on_anim_value_changed(self, value):
        self.anim_progress = float(value)
        self.update()

    def _on_anim_finished(self):
        self.is_animating = False
        self.anim_moving_pieces = []
        self.anim_target_squares = set()
        self.anim_captured_info = None
        self.anim_progress = 1.0
        self.update()
        if self._anim_on_finished is not None:
            cb = self._anim_on_finished
            self._anim_on_finished = None
            cb()

    def reset_animation(self):
        """Immediately stop any running animation and reset animation state."""
        if self.move_anim.state() == QVariantAnimation.State.Running:
            self.move_anim.stop()
        self.is_animating = False
        self.anim_moving_pieces = []
        self.anim_target_squares = set()
        self.anim_captured_info = None
        self._anim_on_finished = None
        self.anim_progress = 0.0
        self.update()

    def animate_and_push_move(self, move: chess.Move, on_finished=None):
        """Prepare move animation details, push move to board, and start smooth animation."""
        self.reset_animation()

        moving_piece = self.board.piece_at(move.from_square)
        if moving_piece is None:
            self.board.push(move)
            self.last_move = move
            self.update()
            if on_finished:
                on_finished()
            return

        moving_pieces: list[tuple[chess.Piece, int, int]] = []
        captured_info: tuple[chess.Piece, int] | None = None

        if self.board.is_castling(move):
            moving_pieces.append((moving_piece, move.from_square, move.to_square))
            if self.board.is_kingside_castling(move):
                r_from = chess.H1 if self.board.turn == chess.WHITE else chess.H8
                r_to = chess.F1 if self.board.turn == chess.WHITE else chess.F8
            else:
                r_from = chess.A1 if self.board.turn == chess.WHITE else chess.A8
                r_to = chess.D1 if self.board.turn == chess.WHITE else chess.D8
            r_piece = self.board.piece_at(r_from)
            if r_piece is not None:
                moving_pieces.append((r_piece, r_from, r_to))
        elif self.board.is_en_passant(move):
            moving_pieces.append((moving_piece, move.from_square, move.to_square))
            cap_sq = chess.square(chess.square_file(move.to_square), chess.square_rank(move.from_square))
            cap_piece = self.board.piece_at(cap_sq)
            if cap_piece is not None:
                captured_info = (cap_piece, cap_sq)
        elif self.board.is_capture(move):
            moving_pieces.append((moving_piece, move.from_square, move.to_square))
            cap_piece = self.board.piece_at(move.to_square)
            if cap_piece is not None:
                captured_info = (cap_piece, move.to_square)
        else:
            moving_pieces.append((moving_piece, move.from_square, move.to_square))

        # Push to authoritative chess board
        self.board.push(move)
        self.last_move = move
        self.selected_square = None
        self.legal_moves_for_selected = []

        # Configure animation
        self.anim_moving_pieces = moving_pieces
        self.anim_target_squares = {m[2] for m in moving_pieces}
        self.anim_captured_info = captured_info
        self._anim_on_finished = on_finished
        self.is_animating = True
        self.anim_progress = 0.0

        self.move_anim.start()

    # ----- coordinate helpers -----
    def _geometry(self):
        board_total = min(self.width(), self.height()) - 16.0
        origin_x = (self.width() - board_total) / 2.0
        origin_y = (self.height() - board_total) / 2.0
        margin = max(34.0, board_total * 0.058)
        sq_size = (board_total - 2.0 * margin) / 8.0
        grid_x = origin_x + margin
        grid_y = origin_y + margin
        return board_total, origin_x, origin_y, margin, sq_size, grid_x, grid_y

    def _square_rect(self, sq: int) -> QRectF:
        board_total, origin_x, origin_y, margin, sq_size, grid_x, grid_y = self._geometry()
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        if self.flipped:
            col = 7 - file
            row = rank
        else:
            col = file
            row = 7 - rank
        x = grid_x + col * sq_size
        y = grid_y + row * sq_size
        return QRectF(x, y, sq_size, sq_size)

    def _pos_to_square(self, pos) -> int | None:
        board_total, origin_x, origin_y, margin, sq_size, grid_x, grid_y = self._geometry()
        x = pos.x() - grid_x
        y = pos.y() - grid_y
        if x < 0 or y < 0:
            return None
        col = int(x / sq_size)
        row = int(y / sq_size)
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
        painter.setClipping(False)

        board_total, origin_x, origin_y, margin, sq_size, grid_x, grid_y = self._geometry()
        ss = sq_size

        # ──── 3D Driftwood & Brass Frame ────
        frame_rect = QRectF(origin_x, origin_y, board_total, board_total)

        # Outer driftwood border gradient
        wood_grad = QLinearGradient(origin_x, origin_y, origin_x + board_total, origin_y + board_total)
        wood_grad.setColorAt(0.0, QColor("#8D6E63"))
        wood_grad.setColorAt(0.2, QColor("#A08070"))
        wood_grad.setColorAt(0.4, QColor("#6D4C3D"))
        wood_grad.setColorAt(0.6, QColor("#9E8070"))
        wood_grad.setColorAt(0.8, QColor("#7D5E4F"))
        wood_grad.setColorAt(1.0, QColor("#8D6E63"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(wood_grad))
        border_path = QPainterPath()
        border_path.addRoundedRect(frame_rect, 6, 6)
        painter.drawPath(border_path)

        # Wood grain texture lines (subtle diagonal)
        painter.save()
        painter.setClipPath(border_path)
        painter.setPen(QPen(QColor(0, 0, 0, 18), 0.5))
        start_i = int(origin_x) - 20
        end_i = int(origin_x + board_total) + 40
        for i in range(start_i, end_i, 4):
            painter.drawLine(QPointF(i, origin_y), QPointF(i - 15, origin_y + board_total))
        painter.restore()

        # Inner beveled gold/coral trim line
        inner_frame = QRectF(grid_x - 2.5, grid_y - 2.5, 8 * sq_size + 5, 8 * sq_size + 5)
        painter.setPen(QPen(QColor("#D4AF37"), 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(inner_frame)

        # Subtle coral inner highlight
        inner_frame2 = QRectF(grid_x - 0.5, grid_y - 0.5, 8 * sq_size + 1, 8 * sq_size + 1)
        painter.setPen(QPen(QColor(231, 111, 81, 80), 0.8))
        painter.drawRect(inner_frame2)

        # ──── Coordinate labels (nautical gold/sand) ────
        coord_color = QColor(COLORS.get("coord_text", "#D4AF37"))
        font = QFont("Segoe UI")
        font.setPixelSize(max(12, int(margin * 0.46)))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(coord_color)

        for col in range(8):
            file_idx = (7 - col) if self.flipped else col
            file_label = chr(ord("a") + file_idx)
            # Top
            top_rect = QRectF(grid_x + col * sq_size, origin_y, sq_size, margin)
            painter.drawText(top_rect, Qt.AlignmentFlag.AlignCenter, file_label)
            # Bottom
            bottom_rect = QRectF(grid_x + col * sq_size, grid_y + 8 * sq_size, sq_size, margin)
            painter.drawText(bottom_rect, Qt.AlignmentFlag.AlignCenter, file_label)

        for row in range(8):
            rank_idx = row if self.flipped else (7 - row)
            rank_label = str(rank_idx + 1)
            # Left
            left_rect = QRectF(origin_x, grid_y + row * sq_size, margin, sq_size)
            painter.drawText(left_rect, Qt.AlignmentFlag.AlignCenter, rank_label)
            # Right
            right_rect = QRectF(grid_x + 8 * sq_size, grid_y + row * sq_size, margin, sq_size)
            painter.drawText(right_rect, Qt.AlignmentFlag.AlignCenter, rank_label)

        # ──── Squares with textured gradients ────
        for sq in chess.SQUARES:
            rect = self._square_rect(sq)
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)
            is_light = (file + rank) % 2 == 1

            if is_light:
                # Warm sunlit sand gradient
                sq_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
                sq_grad.setColorAt(0.0, QColor("#FAF0CA"))
                sq_grad.setColorAt(1.0, QColor("#EAD2AC"))
                painter.setBrush(QBrush(sq_grad))
            else:
                # Deep tropical lagoon gradient
                sq_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
                sq_grad.setColorAt(0.0, QColor("#1D7874"))
                sq_grad.setColorAt(1.0, QColor("#13505B"))
                painter.setBrush(QBrush(sq_grad))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)

            # Delicate inner border for light squares
            if is_light:
                painter.setPen(QPen(QColor(212, 175, 55, 30), 0.5))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRect(rect.adjusted(1, 1, -1, -1))
            else:
                # Subtle diagonal water-shimmer highlight on dark squares
                shimmer_path = QPainterPath()
                shimmer_path.moveTo(rect.topRight())
                shimmer_path.lineTo(rect.right() - ss * 0.35, rect.top())
                shimmer_path.lineTo(rect.left(), rect.bottom() - ss * 0.35)
                shimmer_path.lineTo(rect.bottomLeft())
                shimmer_path.lineTo(rect.left() + ss * 0.35, rect.bottom())
                shimmer_path.lineTo(rect.right(), rect.top() + ss * 0.35)
                shimmer_path.closeSubpath()
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(128, 255, 219, 10)))
                painter.drawPath(shimmer_path)

        # ──── Last move highlight: warm sunset coral-amber ────
        if self.last_move is not None:
            lm_color = QColor(244, 162, 97, 115)  # rgba(244, 162, 97, 0.45)
            painter.setBrush(QBrush(lm_color))
            painter.setPen(Qt.PenStyle.NoPen)
            for sq in (self.last_move.from_square, self.last_move.to_square):
                painter.drawRect(self._square_rect(sq))

        # ──── Selected square highlight: glowing golden-aqua ring ────
        if not self.is_animating and self.selected_square is not None:
            sel_rect = self._square_rect(self.selected_square)
            # Golden fill
            sel_color = QColor(212, 175, 55, 80)
            painter.setBrush(QBrush(sel_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(sel_rect)
            # Golden-aqua ring
            ring_pen = QPen(QColor("#D4AF37"), max(2, ss * 0.06))
            ring_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(sel_rect.adjusted(1.5, 1.5, -1.5, -1.5))

        # ──── Check highlight: pulsing crimson-coral radial glow ────
        if not self.is_animating and self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            if king_sq is not None:
                kr = self._square_rect(king_sq)
                center = kr.center()
                radius = ss * 0.52
                check_grad = QRadialGradient(center, radius)
                check_grad.setColorAt(0.0, QColor(230, 57, 70, 180))
                check_grad.setColorAt(0.4, QColor(231, 111, 81, 120))
                check_grad.setColorAt(0.7, QColor(244, 162, 97, 60))
                check_grad.setColorAt(1.0, QColor(244, 162, 97, 0))
                painter.setBrush(QBrush(check_grad))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(center, radius, radius)
                # Crisp ring
                painter.setPen(QPen(QColor(230, 57, 70, 160), max(1.5, ss * 0.04)))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, ss * 0.44, ss * 0.44)

        # ──── Static Pieces ────
        for sq in chess.SQUARES:
            # Skip drawing static piece if it's currently at an animation destination square
            if self.is_animating and sq in self.anim_target_squares:
                continue

            piece = self.board.piece_at(sq)
            if piece is None:
                continue

            renderer = PieceRendererCache.get(piece.color, piece.piece_type)
            if renderer is None:
                continue

            rect = self._square_rect(sq)
            # Slight padding so pieces don't touch the edges
            padding = ss * 0.06
            piece_rect = rect.adjusted(padding, padding, -padding, -padding)
            renderer.render(painter, piece_rect)

        # ──── Captured Piece (dissolves into sea mist on impact) ────
        if self.is_animating and self.anim_captured_info is not None:
            cap_piece, cap_sq = self.anim_captured_info
            if self.anim_progress < 0.65:
                cap_opacity = 1.0
            elif self.anim_progress < 0.88:
                cap_opacity = max(0.0, (0.88 - self.anim_progress) / 0.23)
            else:
                cap_opacity = 0.0

            if cap_opacity > 0.0:
                renderer = PieceRendererCache.get(cap_piece.color, cap_piece.piece_type)
                if renderer:
                    cap_rect = self._square_rect(cap_sq)
                    padding = ss * 0.06
                    cap_piece_rect = cap_rect.adjusted(padding, padding, -padding, -padding)
                    painter.save()
                    painter.setOpacity(cap_opacity)
                    renderer.render(painter, cap_piece_rect)
                    painter.restore()

        # ──── Animating Pieces (rendered smoothly on top with subtle marine breeze lift) ────
        if self.is_animating and self.anim_moving_pieces:
            for piece, from_sq, to_sq in self.anim_moving_pieces:
                start_rect = self._square_rect(from_sq)
                end_rect = self._square_rect(to_sq)

                t = self.anim_progress
                cur_x = start_rect.x() + (end_rect.x() - start_rect.x()) * t
                cur_y = start_rect.y() + (end_rect.y() - start_rect.y()) * t
                cur_w = start_rect.width() + (end_rect.width() - start_rect.width()) * t
                cur_h = start_rect.height() + (end_rect.height() - start_rect.height()) * t
                cur_rect = QRectF(cur_x, cur_y, cur_w, cur_h)

                padding = ss * 0.06
                piece_rect = cur_rect.adjusted(padding, padding, -padding, -padding)

                # Marine lift shadow underneath flying piece
                lift = 1.0 - abs(t - 0.5) * 0.6
                shadow_offset = ss * 0.04 * lift
                shadow_rect = piece_rect.translated(shadow_offset, shadow_offset * 1.2)
                painter.save()
                shadow_color = QColor(7, 26, 36, int(60 * lift))
                painter.setBrush(QBrush(shadow_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(shadow_rect.center(), piece_rect.width() * 0.38, piece_rect.height() * 0.38)
                painter.restore()

                renderer = PieceRendererCache.get(piece.color, piece.piece_type)
                if renderer:
                    renderer.render(painter, piece_rect)

        # ──── Legal move indicators ────
        if not self.is_animating and self.selected_square is not None:
            for move in self.legal_moves_for_selected:
                target_rect = self._square_rect(move.to_square)
                center = target_rect.center()
                target_piece = self.board.piece_at(move.to_square)

                if target_piece is not None:
                    # Capture indicator: coral-ringed target on capturable enemy pieces
                    painter.setPen(QPen(QColor("#E76F51"), max(2.5, ss * 0.07)))
                    painter.setBrush(QBrush(QColor(231, 111, 81, 35)))
                    painter.drawEllipse(center, ss * 0.42, ss * 0.42)
                    # Inner ring
                    painter.setPen(QPen(QColor(244, 162, 97, 120), max(1, ss * 0.03)))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(center, ss * 0.35, ss * 0.35)
                else:
                    # Empty square: translucent water-droplet / ripple ring
                    # Outer ripple
                    painter.setPen(QPen(QColor(128, 255, 219, 80), max(1, ss * 0.025)))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawEllipse(center, ss * 0.22, ss * 0.22)
                    # Inner filled droplet
                    painter.setPen(Qt.PenStyle.NoPen)
                    drop_grad = QRadialGradient(center, ss * 0.16)
                    drop_grad.setColorAt(0.0, QColor(128, 255, 219, 160))
                    drop_grad.setColorAt(0.6, QColor(128, 255, 219, 90))
                    drop_grad.setColorAt(1.0, QColor(128, 255, 219, 30))
                    painter.setBrush(QBrush(drop_grad))
                    painter.drawEllipse(center, ss * 0.14, ss * 0.14)

        painter.end()

    # ----- interaction -----
    def mousePressEvent(self, event):
        if not self.interactive or self.is_animating:
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
# CentralBackground — paints immersive coastal beach panorama
# ═══════════════════════════════════════════════════════════════════════════
class CentralBackground(QWidget):
    """Central widget that paints an attractive tropical beach & ocean resort panorama."""

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = float(self.width())
        h = float(self.height())

        # ──── 1. Sunlit Tropical Sky (y = 0 to 0.38 * h) ────
        sky_h = 0.38 * h
        sky_grad = QLinearGradient(0, 0, 0, sky_h)
        sky_grad.setColorAt(0.0, QColor("#1E88E5"))   # Top azure
        sky_grad.setColorAt(0.55, QColor("#4DD0E1"))  # Mid cyan
        sky_grad.setColorAt(1.0, QColor("#FFF59D"))   # Warm horizon glow
        painter.fillRect(QRectF(0, 0, w, sky_h), sky_grad)

        # Glowing Sun centered at (0.72 * w, 0.14 * h) with radius 0.12 * w
        sun_cx = 0.72 * w
        sun_cy = 0.14 * h
        sun_r = 0.12 * w
        sun_grad = QRadialGradient(sun_cx, sun_cy, sun_r)
        sun_grad.setColorAt(0.0, QColor("#FFFFFF"))
        sun_grad.setColorAt(0.35, QColor("#FFE082"))
        sun_grad.setColorAt(1.0, QColor(255, 224, 130, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(sun_grad))
        painter.drawEllipse(QPointF(sun_cx, sun_cy), sun_r, sun_r)

        # Soft Clouds (3 layered translucent white cloud silhouettes)
        cloud_color = QColor(255, 255, 255, 90)  # rgba(255, 255, 255, 0.35)
        painter.setBrush(QBrush(cloud_color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Cloud 1: left sky
        c1 = QPainterPath()
        c1.moveTo(0.08 * w, 0.15 * h)
        c1.cubicTo(0.12 * w, 0.10 * h, 0.20 * w, 0.10 * h, 0.24 * w, 0.14 * h)
        c1.cubicTo(0.28 * w, 0.11 * h, 0.34 * w, 0.12 * h, 0.36 * w, 0.16 * h)
        c1.cubicTo(0.38 * w, 0.18 * h, 0.36 * w, 0.22 * h, 0.30 * w, 0.22 * h)
        c1.cubicTo(0.24 * w, 0.23 * h, 0.12 * w, 0.22 * h, 0.08 * w, 0.18 * h)
        c1.closeSubpath()
        painter.drawPath(c1)

        # Cloud 2: center/near sun
        c2 = QPainterPath()
        c2.moveTo(0.44 * w, 0.18 * h)
        c2.cubicTo(0.48 * w, 0.13 * h, 0.54 * w, 0.12 * h, 0.58 * w, 0.16 * h)
        c2.cubicTo(0.62 * w, 0.13 * h, 0.68 * w, 0.15 * h, 0.70 * w, 0.19 * h)
        c2.cubicTo(0.72 * w, 0.23 * h, 0.66 * w, 0.25 * h, 0.60 * w, 0.24 * h)
        c2.cubicTo(0.52 * w, 0.25 * h, 0.46 * w, 0.23 * h, 0.44 * w, 0.18 * h)
        c2.closeSubpath()
        painter.drawPath(c2)

        # Cloud 3: far left / lower horizon
        c3 = QPainterPath()
        c3.moveTo(0.0 * w, 0.24 * h)
        c3.cubicTo(0.04 * w, 0.20 * h, 0.10 * w, 0.19 * h, 0.14 * w, 0.23 * h)
        c3.cubicTo(0.18 * w, 0.21 * h, 0.22 * w, 0.23 * h, 0.24 * w, 0.27 * h)
        c3.cubicTo(0.25 * w, 0.30 * h, 0.18 * w, 0.32 * h, 0.12 * w, 0.31 * h)
        c3.cubicTo(0.06 * w, 0.32 * h, 0.0 * w, 0.30 * h, 0.0 * w, 0.24 * h)
        c3.closeSubpath()
        painter.drawPath(c3)

        # ──── 2. Distant Tropical Island on the Horizon (y = 0.36 * h) ────
        island_path = QPainterPath()
        island_path.moveTo(0.52 * w, 0.38 * h)
        island_path.cubicTo(0.58 * w, 0.36 * h, 0.64 * w, 0.32 * h, 0.68 * w, 0.31 * h)
        island_path.cubicTo(0.72 * w, 0.31 * h, 0.75 * w, 0.34 * h, 0.78 * w, 0.33 * h)
        island_path.cubicTo(0.82 * w, 0.32 * h, 0.85 * w, 0.36 * h, 0.88 * w, 0.38 * h)
        island_path.lineTo(0.88 * w, 0.39 * h)
        island_path.lineTo(0.52 * w, 0.39 * h)
        island_path.closeSubpath()

        island_grad = QLinearGradient(0.52 * w, 0.31 * h, 0.88 * w, 0.38 * h)
        island_grad.setColorAt(0.0, QColor("#004D40"))
        island_grad.setColorAt(1.0, QColor("#00695C"))
        painter.setBrush(QBrush(island_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPath(island_path)

        # ──── 3. Multi-Layered Turquoise Ocean & Diagonal Shoreline (y = 0.36 * h to 0.78 * h) ────
        ocean_grad = QLinearGradient(0, 0.36 * h, 0, h)
        ocean_grad.setColorAt(0.0, QColor("#005F73"))   # Deep ocean
        ocean_grad.setColorAt(0.40, QColor("#0A9396"))  # Mid turquoise
        ocean_grad.setColorAt(1.0, QColor("#94D2BD"))   # Shallow aqua
        painter.fillRect(QRectF(0, 0.36 * h, w, 0.64 * h), ocean_grad)

        # 10 subtle shimmering water sun-glints (rgba(255, 255, 255, 0.25)) between 0.38 * h and 0.55 * h
        glint_color = QColor(255, 255, 255, 64)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glint_color))
        glints = [
            (0.68 * w, 0.39 * h, 28, 2.5),
            (0.74 * w, 0.41 * h, 36, 2.0),
            (0.64 * w, 0.43 * h, 22, 2.0),
            (0.71 * w, 0.44 * h, 42, 2.5),
            (0.58 * w, 0.46 * h, 30, 2.0),
            (0.77 * w, 0.47 * h, 25, 2.0),
            (0.66 * w, 0.49 * h, 38, 2.2),
            (0.52 * w, 0.51 * h, 20, 1.8),
            (0.73 * w, 0.52 * h, 32, 2.0),
            (0.62 * w, 0.54 * h, 26, 2.0),
        ]
        for gx, gy, gw, gh in glints:
            painter.drawRoundedRect(QRectF(gx, gy, gw, gh), gh / 2.0, gh / 2.0)

        # 3 sweeping diagonal S-curve wave layers running from (0, 0.62 * h) across to (w, 0.46 * h)
        # Layer 1: Back wave crest (#48CAE4)
        w1 = QPainterPath()
        w1.moveTo(0, 0.60 * h)
        w1.cubicTo(0.35 * w, 0.65 * h, 0.65 * w, 0.49 * h, w, 0.44 * h)
        w1.lineTo(w, h)
        w1.lineTo(0, h)
        w1.closeSubpath()
        painter.setBrush(QBrush(QColor("#48CAE4")))
        painter.drawPath(w1)

        # Layer 2: Shallow lagoon wave (#90E0EF)
        w2 = QPainterPath()
        w2.moveTo(0, 0.63 * h)
        w2.cubicTo(0.38 * w, 0.68 * h, 0.68 * w, 0.52 * h, w, 0.47 * h)
        w2.lineTo(w, h)
        w2.lineTo(0, h)
        w2.closeSubpath()
        painter.setBrush(QBrush(QColor("#90E0EF")))
        painter.drawPath(w2)

        # Layer 3: Creamy white seafoam surf edge (pen thickness 4px + translucent fill rgba(255, 255, 255, 0.75))
        w3 = QPainterPath()
        w3.moveTo(0, 0.66 * h)
        w3.cubicTo(0.36 * w, 0.70 * h, 0.66 * w, 0.54 * h, w, 0.49 * h)
        w3.lineTo(w, h)
        w3.lineTo(0, h)
        w3.closeSubpath()
        painter.setPen(QPen(QColor(255, 255, 255, 220), 4.0))
        painter.setBrush(QBrush(QColor(255, 255, 255, 190)))
        painter.drawPath(w3)

        # ──── 4. Warm Golden Sand Beach, Palm Tree & Starfish (y = 0.46 * h to h) ────
        sand_path = QPainterPath()
        sand_path.moveTo(0, 0.68 * h)
        sand_path.cubicTo(0.36 * w, 0.72 * h, 0.66 * w, 0.56 * h, w, 0.51 * h)
        sand_path.lineTo(w, h)
        sand_path.lineTo(0, h)
        sand_path.closeSubpath()

        sand_grad = QLinearGradient(0, 0.50 * h, 0, h)
        sand_grad.setColorAt(0.0, QColor("#F6E2B3"))
        sand_grad.setColorAt(0.50, QColor("#E6C280"))
        sand_grad.setColorAt(1.0, QColor("#D4A373"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(sand_grad))
        painter.drawPath(sand_path)

        # ──── Palm Tree Silhouette on Right Shore (around x = 0.68 * w) ────
        # Soft diagonal shadow cast on the sand (rgba(93, 64, 55, 0.18))
        shadow = QPainterPath()
        shadow.moveTo(0.73 * w, 0.88 * h)
        shadow.cubicTo(0.78 * w, 0.89 * h, 0.84 * w, 0.92 * h, 0.88 * w, 0.94 * h)
        shadow.cubicTo(0.85 * w, 0.96 * h, 0.76 * w, 0.92 * h, 0.74 * w, 0.88 * h)
        shadow.closeSubpath()
        painter.setBrush(QBrush(QColor(93, 64, 55, 46)))
        painter.drawPath(shadow)

        # Gracefully curved brown coconut trunk (#5D4037 / #8D6E63)
        # Rising from (0.74 * w, 0.88 * h) up to (0.66 * w, 0.22 * h)
        trunk = QPainterPath()
        trunk.moveTo(0.73 * w, 0.88 * h)
        trunk.cubicTo(0.72 * w, 0.65 * h, 0.69 * w, 0.42 * h, 0.656 * w, 0.22 * h)
        trunk.lineTo(0.664 * w, 0.22 * h)
        trunk.cubicTo(0.70 * w, 0.42 * h, 0.735 * w, 0.65 * h, 0.75 * w, 0.88 * h)
        trunk.closeSubpath()

        trunk_grad = QLinearGradient(0.74 * w, 0.88 * h, 0.66 * w, 0.22 * h)
        trunk_grad.setColorAt(0.0, QColor("#5D4037"))
        trunk_grad.setColorAt(0.6, QColor("#6D4C41"))
        trunk_grad.setColorAt(1.0, QColor("#8D6E63"))
        painter.setBrush(QBrush(trunk_grad))
        painter.drawPath(trunk)

        # Coconut trunk rings / texture
        painter.setPen(QPen(QColor(60, 40, 30, 80), 1.2))
        for t in [0.35, 0.45, 0.55, 0.65, 0.75, 0.82]:
            tx = (1 - t) * (0.74 * w) + t * (0.66 * w) - 2
            ty = (1 - t) * (0.88 * h) + t * (0.22 * h)
            tw = 12 * (1 - 0.4 * t)
            painter.drawLine(QPointF(tx - tw / 2, ty), QPointF(tx + tw / 2, ty + 1))

        # 3 Coconuts at crown (0.66 * w, 0.22 * h)
        crown_x = 0.66 * w
        crown_y = 0.22 * h
        painter.setPen(QPen(QColor("#3E2723"), 1.0))
        painter.setBrush(QBrush(QColor("#4E342E")))
        painter.drawEllipse(QPointF(crown_x - 3.5, crown_y + 3), 4.5, 5.0)
        painter.drawEllipse(QPointF(crown_x + 3.5, crown_y + 3), 4.5, 5.0)
        painter.drawEllipse(QPointF(crown_x, crown_y + 6), 4.0, 4.5)

        # 7 Lush arching palm fronds radiating from top of trunk in tropical greens
        frond_colors = [
            QColor("#1B5E20"), QColor("#2E7D32"), QColor("#388E3C"),
            QColor("#43A047"), QColor("#2E7D32"), QColor("#1B5E20"), QColor("#388E3C")
        ]
        frond_curves = [
            # (dx_ctrl, dy_ctrl, dx_tip, dy_tip) relative to crown
            (-0.11 * w, -0.06 * h, -0.15 * w, -0.01 * h),   # 1. arch left-up
            (-0.13 * w, -0.01 * h, -0.16 * w, 0.08 * h),    # 2. arch left-mid
            (-0.09 * w, 0.06 * h, -0.12 * w, 0.16 * h),     # 3. arch left-down
            (-0.02 * w, -0.10 * h, 0.0 * w, -0.12 * h),     # 4. arch straight up
            (0.08 * w, -0.08 * h, 0.13 * w, -0.03 * h),     # 5. arch right-up
            (0.12 * w, -0.02 * h, 0.15 * w, 0.07 * h),      # 6. arch right-mid
            (0.09 * w, 0.06 * h, 0.11 * w, 0.15 * h),       # 7. arch right-down
        ]

        for idx, (fc, (cx_c, cy_c, tx_c, ty_c)) in enumerate(zip(frond_colors, frond_curves)):
            tip_x = crown_x + tx_c
            tip_y = crown_y + ty_c
            ctrl_x = crown_x + cx_c
            ctrl_y = crown_y + cy_c

            blade = QPainterPath()
            blade.moveTo(crown_x, crown_y)
            blade.cubicTo(ctrl_x - 3, ctrl_y - 4, tip_x - 2, tip_y - 2, tip_x, tip_y)
            blade.cubicTo(tip_x + 2, tip_y + 2, ctrl_x + 4, ctrl_y + 5, crown_x, crown_y)
            blade.closeSubpath()

            painter.setPen(QPen(fc.darker(120), 0.8))
            painter.setBrush(QBrush(fc))
            painter.drawPath(blade)

            # Central vein stroke
            painter.setPen(QPen(QColor(255, 255, 255, 70), 1.0))
            painter.drawLine(QPointF(crown_x, crown_y), QPointF(tip_x, tip_y))

        # ──── Foreground Starfish & Seashell (lower-right sand 0.62 * w, 0.85 * h) ────
        star_cx = 0.62 * w
        star_cy = 0.85 * h
        star_r = 13.0
        star_inner = 5.2

        star_path = QPainterPath()
        for i in range(10):
            angle = -math.pi / 2.0 + i * (math.pi / 5.0)
            rad = star_r if i % 2 == 0 else star_inner
            px = star_cx + rad * math.cos(angle)
            py = star_cy + rad * math.sin(angle)
            if i == 0:
                star_path.moveTo(px, py)
            else:
                star_path.lineTo(px, py)
        star_path.closeSubpath()

        painter.setPen(QPen(QColor("#C04B33"), 1.2))
        painter.setBrush(QBrush(QColor("#E76F51")))
        painter.drawPath(star_path)

        # Starfish center dots
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FFF59D")))
        painter.drawEllipse(QPointF(star_cx, star_cy), 2.2, 2.2)

        # White seashell resting next to starfish (0.65 * w, 0.87 * h)
        shell_cx = 0.65 * w
        shell_cy = 0.87 * h
        shell_path = QPainterPath()
        shell_path.moveTo(shell_cx - 7, shell_cy + 4)
        shell_path.cubicTo(shell_cx - 9, shell_cy - 6, shell_cx + 9, shell_cy - 6, shell_cx + 7, shell_cy + 4)
        shell_path.cubicTo(shell_cx + 3, shell_cy + 7, shell_cx - 3, shell_cy + 7, shell_cx - 7, shell_cy + 4)
        shell_path.closeSubpath()

        shell_grad = QLinearGradient(shell_cx, shell_cy - 6, shell_cx, shell_cy + 6)
        shell_grad.setColorAt(0.0, QColor("#FFFFFF"))
        shell_grad.setColorAt(0.7, QColor("#FFF8EE"))
        shell_grad.setColorAt(1.0, QColor("#EAD2AC"))
        painter.setPen(QPen(QColor("#BCAAA4"), 1.0))
        painter.setBrush(QBrush(shell_grad))
        painter.drawPath(shell_path)

        # Seashell ridges
        painter.setPen(QPen(QColor("#D4AF37"), 0.8))
        painter.drawLine(QPointF(shell_cx, shell_cy + 6), QPointF(shell_cx - 5, shell_cy - 3))
        painter.drawLine(QPointF(shell_cx, shell_cy + 6), QPointF(shell_cx - 5, shell_cy - 5))
        painter.drawLine(QPointF(shell_cx, shell_cy + 6), QPointF(shell_cx + 5, shell_cy - 3))

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

        # AI pacing, synchronization, and animation state
        self.is_busy: bool = False
        self.ai_search_id: int = 0
        self.pending_ai_move: tuple[chess.Move, int] | None = None
        self.ai_delay_elapsed: bool = False

        self.ai_delay_timer = QTimer(self)
        self.ai_delay_timer.setSingleShot(True)
        self.ai_delay_timer.timeout.connect(self._on_ai_delay_timeout)

        self.ai_pause_timer = QTimer(self)
        self.ai_pause_timer.setSingleShot(True)
        self.ai_pause_timer.timeout.connect(self._on_ai_pause_timeout)

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

    def set_busy_state(self, busy: bool):
        """Update UI interaction state when busy animating or during AI turns."""
        self.is_busy = busy
        self.chess_board.interactive = not busy and (self.board.turn == self.player_color) and not self.board.is_game_over()
        self.undo_btn.setEnabled(not busy and len(self.board.move_stack) > 0 and not self.board.is_game_over())
        self.flip_btn.setEnabled(not busy)
        self.color_combo.setEnabled(not busy)
        self.difficulty_combo.setEnabled(not busy)
        self.new_game_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Color change
    # ------------------------------------------------------------------
    def _on_color_changed(self, index: int):
        if self.is_busy:
            return
        self.player_color = chess.WHITE if index == 0 else chess.BLACK
        self.chess_board.player_color = self.player_color
        self.new_game()

    # ------------------------------------------------------------------
    # Game actions and Animation / AI Orchestration
    # ------------------------------------------------------------------
    def on_player_move(self, move: chess.Move):
        """Called when the human makes a move on the board."""
        if self.is_busy:
            return

        self.set_busy_state(True)

        # Check whether this move concludes the game
        board_copy = copy.deepcopy(self.board)
        board_copy.push(move)
        game_ends = board_copy.is_game_over()

        # If the game continues, start the AI calculation immediately in background thread
        # (AI calculation runs at full speed without artificial throttling)
        if not game_ends:
            self._start_ai_search(board_copy)

        # Smoothly animate the player's piece movement
        self.chess_board.animate_and_push_move(
            move,
            on_finished=lambda: self._on_player_move_finished(game_ends)
        )

    def _start_ai_search(self, board_copy: chess.Board):
        """Launch the engine search on a background thread."""
        self.ai_search_id += 1
        search_id = self.ai_search_id
        self.pending_ai_move = None
        self.ai_delay_elapsed = False

        difficulty_key = self.difficulty_combo.currentText()
        difficulty = DIFFICULTY_MAP.get(difficulty_key, "Beach Breeze")

        self.ai_worker = AIWorker(board_copy, difficulty, self.engine, parent=self)
        self.ai_worker.result_ready.connect(
            lambda move, score, s_id=search_id: self._on_ai_worker_ready(move, score, s_id)
        )
        self.ai_worker.start()

    def _on_player_move_finished(self, game_ends: bool):
        """Called when player piece movement animation completes."""
        self.update_move_history()
        self.update_captured_pieces()
        self.eval_bar.set_eval(self.engine.evaluate(self.board))

        if self.check_game_over():
            self.set_busy_state(False)
            self.chess_board.interactive = False
            return

        # Player move landed cleanly; start AI presentation delay
        self.status_label.setText("AI is thinking in the waves... 🌊")
        self.ai_delay_timer.start(AI_PRE_MOVE_DELAY_MS)

    def _on_ai_worker_ready(self, move: chess.Move, eval_score: int, search_id: int):
        """Called when background AI calculation finishes."""
        if search_id != self.ai_search_id:
            return  # Discard stale result from cancelled search

        self.pending_ai_move = (move, eval_score)

        # If the presentation delay timer already elapsed, execute the AI move now
        if self.ai_delay_elapsed:
            self._execute_ai_move()

    def _on_ai_delay_timeout(self):
        """Called when the AI pre-move thinking delay finishes."""
        self.ai_delay_elapsed = True

        # If the AI calculation is already done, execute the move now
        if self.pending_ai_move is not None:
            self._execute_ai_move()
        else:
            # AI is still calculating (higher difficulty / deep search)
            self.status_label.setText("AI is pondering deeply... 🌊")

    def _execute_ai_move(self):
        """Trigger the AI's move animation and presentation."""
        if self.pending_ai_move is None:
            return

        move, eval_score = self.pending_ai_move
        self.pending_ai_move = None
        self.ai_worker = None

        if move is None or move not in self.board.legal_moves:
            self.set_busy_state(False)
            self.update_display()
            self.check_game_over()
            return

        # Record SAN before pushing the move
        san = self.board.san(move)
        self.last_eval = eval_score
        self.eval_bar.set_eval(eval_score)
        self.status_label.setText(f"AI plays {san} 🌊")

        # Smoothly animate AI piece movement
        self.chess_board.animate_and_push_move(
            move,
            on_finished=lambda: self._on_ai_move_finished(san)
        )

    def _on_ai_move_finished(self, san: str):
        """Called when AI move animation finishes."""
        self.update_move_history()
        self.update_captured_pieces()

        if self.check_game_over():
            self.set_busy_state(False)
            self.chess_board.interactive = False
            return

        # Brief visual pause so the player clearly registers the AI's move
        self.status_label.setText(f"AI played {san} 🌊")
        self.ai_pause_timer.start(AI_POST_MOVE_PAUSE_MS)

    def _on_ai_pause_timeout(self):
        """Called when post-move pause finishes; restores player control."""
        if self.check_game_over():
            self.set_busy_state(False)
            self.chess_board.interactive = False
            return

        self.set_busy_state(False)
        self._update_status()

    def new_game(self):
        """Reset everything for a fresh game."""
        # Cancel any pending AI operations and timers
        self.ai_search_id += 1
        self.ai_delay_timer.stop()
        self.ai_pause_timer.stop()
        self.pending_ai_move = None
        self.ai_delay_elapsed = False

        if self.ai_worker is not None and self.ai_worker.isRunning():
            self.ai_worker.terminate()
            self.ai_worker.wait(500)
            self.ai_worker = None

        self.chess_board.reset_animation()

        self.board.reset()
        self.engine.reset()
        self.chess_board.board = self.board
        self.chess_board.player_color = self.player_color
        self.chess_board.last_move = None
        self.chess_board.selected_square = None
        self.chess_board.legal_moves_for_selected = []
        self.last_eval = 0
        self.eval_bar.set_eval(0)

        if self.player_color == chess.BLACK:
            self.chess_board.flipped = True
            self.set_busy_state(True)
            self.status_label.setText("AI is thinking in the waves... 🌊")
            self.update_display()
            # Start AI calculation as White for the opening move
            board_copy = copy.deepcopy(self.board)
            self._start_ai_search(board_copy)
            self.ai_delay_timer.start(AI_PRE_MOVE_DELAY_MS)
        else:
            self.chess_board.flipped = False
            self.set_busy_state(False)
            self.update_display()

    def undo_move(self):
        """Undo moves back to the player's turn."""
        if self.is_busy:
            return

        if not self.board.move_stack:
            return

        self.chess_board.reset_animation()

        # If it's the AI's turn (e.g. human moved and AI has not responded yet), pop 1 move
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
        self.set_busy_state(False)
        self.update_display()

    def flip_board(self):
        """Toggle board orientation."""
        if self.is_busy:
            return
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
        if not self.is_busy:
            self.eval_bar.set_eval(self.engine.evaluate(self.board))
        self.set_busy_state(self.is_busy)

    def _update_status(self):
        """Set the status label based on current game state."""
        if self.board.is_game_over():
            return  # status was already set by check_game_over

        if self.board.turn == self.player_color:
            color_name = "White" if self.board.turn == chess.WHITE else "Black"
            if self.board.is_check():
                self.status_label.setText(f"Your Turn — {color_name} in Check! ⚠️")
            else:
                self.status_label.setText(f"Your Turn — {color_name} to Move")
        else:
            self.status_label.setText("AI is thinking in the waves... 🌊")

    def update_move_history(self):
        """Parse board.move_stack into SAN pairs and fill the table."""
        # Replay moves from the board root position to get correct SAN notation
        temp_board = self.board.root()
        san_moves: list[str] = []
        for move in self.board.move_stack:
            try:
                san = temp_board.san(move)
                temp_board.push(move)
            except Exception:
                san = move.uci()
            san_moves.append(san)

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
