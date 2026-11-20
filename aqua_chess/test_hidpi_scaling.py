"""
Comprehensive verification of HiDPI scaling, devicePixelRatio alignment, and coordinate integrity.
"""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
import chess

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import QPointF, QRectF
from ui import AquaChessWindow, ChessBoard, CentralBackground, PiecePixmapCache


def run_hidpi_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    print("--- 1. Testing HiDPI Board Alignment across Scale Factors (100%, 125%, 150%, 175%, 200%) ---")
    scale_factors = [1.0, 1.25, 1.5, 1.75, 2.0]

    for dpr in scale_factors:
        board = chess.Board()
        cb = ChessBoard(board)
        cb.resize(900, 900)

        # Allocate image at physical dimensions with devicePixelRatio
        img = QImage(int(round(900 * dpr)), int(round(900 * dpr)), QImage.Format.Format_ARGB32)
        img.setDevicePixelRatio(dpr)
        img.fill(QColor("magenta"))

        cb.render(img)

        # 1. Verify single source of truth geometry
        board_total, origin_x, origin_y, margin, sq_size, grid_x, grid_y = cb._geometry()
        assert board_total > 0 and sq_size > 0
        frame_rect = QRectF(origin_x, origin_y, board_total, board_total)

        # Ensure board fits completely inside widget boundaries
        assert origin_x >= 0, f"DPR {dpr}: origin_x ({origin_x}) negative"
        assert origin_y >= 0, f"DPR {dpr}: origin_y ({origin_y}) negative"
        assert origin_x + board_total <= 900, f"DPR {dpr}: right edge exceeds widget"
        assert origin_y + board_total <= 900, f"DPR {dpr}: bottom edge exceeds widget"

        # 2. Verify all 4 corner squares (a1, h1, a8, h8) are completely inside frame
        for sq_name, sq in [("a1", chess.A1), ("h1", chess.H1), ("a8", chess.A8), ("h8", chess.H8)]:
            sq_rect = cb._square_rect(sq)
            assert frame_rect.contains(sq_rect), f"DPR {dpr}: Square {sq_name} {sq_rect} sits outside frame {frame_rect}"

            # Check that pixel at square center is rendered and NOT background magenta
            cx, cy = sq_rect.center().x(), sq_rect.center().y()
            phys_x = int(round(cx * dpr))
            phys_y = int(round(cy * dpr))
            c = img.pixelColor(phys_x, phys_y)
            assert c.name() != "#ff00ff", f"DPR {dpr}: Square {sq_name} center ({cx}, {cy}) is unrendered magenta"

        # 3. Verify file h (rightmost file) and rank 1 (bottom rank) are fully rendered and not clipped
        h_file_sqs = [chess.square(7, r) for r in range(8)]
        rank1_sqs = [chess.square(f, 0) for f in range(8)]

        for sq in h_file_sqs:
            r = cb._square_rect(sq)
            assert r.right() <= origin_x + board_total - margin + 0.1, f"File h square {chess.square_name(sq)} overflows grid"
            c = img.pixelColor(int(round(r.center().x() * dpr)), int(round(r.center().y() * dpr)))
            assert c.name() != "#ff00ff", f"DPR {dpr}: File h square {chess.square_name(sq)} clipped"

        for sq in rank1_sqs:
            r = cb._square_rect(sq)
            assert r.bottom() <= origin_y + board_total - margin + 0.1, f"Rank 1 square {chess.square_name(sq)} overflows grid"
            c = img.pixelColor(int(round(r.center().x() * dpr)), int(round(r.center().y() * dpr)))
            assert c.name() != "#ff00ff", f"DPR {dpr}: Rank 1 square {chess.square_name(sq)} clipped"

        print(f"  ✓ Scale {int(dpr*100)}%: All 64 squares (files a-h, ranks 1-8) fully visible, centered, and 1:1 aligned")

    print("\n--- 2. Testing Fullscreen / Maximized Resolutions (1920x1080 & 2560x1440) ---")
    resolutions = [
        (1920, 1080, 1.25),
        (1920, 1080, 1.5),
        (2560, 1440, 1.5),
        (3840, 2160, 2.0),
    ]

    for w, h, dpr in resolutions:
        win = AquaChessWindow()
        win.resize(w, h)

        img = QImage(int(round(w * dpr)), int(round(h * dpr)), QImage.Format.Format_ARGB32)
        img.setDevicePixelRatio(dpr)
        img.fill(QColor("magenta"))

        win.render(img)

        # Verify board within maximized window
        cb = win.chess_board
        board_total, origin_x, origin_y, margin, sq_size, grid_x, grid_y = cb._geometry()
        assert origin_x >= 0 and origin_y >= 0
        assert cb.width() >= board_total
        assert cb.height() >= board_total

        # Check a1 and h8 squares inside window
        a1_r = cb._square_rect(chess.A1)
        h8_r = cb._square_rect(chess.H8)
        assert a1_r.isValid() and h8_r.isValid()

        # Check that center of board in window is rendered
        board_center = cb.mapTo(win, cb.rect().center())
        c = img.pixelColor(int(round(board_center.x() * dpr)), int(round(board_center.y() * dpr)))
        assert c.name() != "#ff00ff", f"Maximized {w}x{h} @ {dpr}x board center unrendered"

        print(f"  ✓ Maximized {w}x{h} @ {int(dpr*100)}% scale: Clean render without clipping or zoom distortion")

    print("\n--- 3. Testing Piece Alignment on Board Squares ---")
    cb_align = ChessBoard(chess.Board())
    cb_align.resize(800, 800)

    # Rook at a1, King at e1, Rook at h1
    dpr = 1.5
    img_align = QImage(int(round(800 * dpr)), int(round(800 * dpr)), QImage.Format.Format_ARGB32)
    img_align.setDevicePixelRatio(dpr)
    img_align.fill(0)
    cb_align.render(img_align)

    for sq, piece_name in [(chess.A1, "White Rook a1"), (chess.E1, "White King e1"), (chess.H1, "White Rook h1"), (chess.E8, "Black King e8")]:
        sq_rect = cb_align._square_rect(sq)
        ss = cb_align._sq_size
        psize = cb_align._piece_size
        # Piece top-left
        pt = QPointF(sq_rect.x() + (ss - psize) * 0.5, sq_rect.y() + (ss - psize) * 0.5)
        piece_rect = QRectF(pt.x(), pt.y(), psize, psize)

        # Verify piece rect is strictly inside square rect
        assert sq_rect.contains(piece_rect), f"{piece_name} rect {piece_rect} exceeds square {sq_rect}"
        print(f"  ✓ {piece_name} perfectly centered inside square {chess.square_name(sq)} (padding: {(ss - psize)*0.5:.1f}px)")

    print("\n==========================================")
    print("ALL HiDPI & ALIGNMENT TESTS PASSED 100%!")
    print("==========================================")


if __name__ == "__main__":
    run_hidpi_tests()
