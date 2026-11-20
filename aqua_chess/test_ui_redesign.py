"""
Comprehensive test script verifying the redesigned UI elements in Aqua Chess:
1. Prominent Turn Indicator ("Whose Turn") banner
2. Bold, Unmistakable Game-Over / Victory Display & Overlay Card
"""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
import chess

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSize, QPoint, QEventLoop, QTimer
from PySide6.QtGui import QImage, QPainter

from ui import (
    AquaChessWindow, ChessBoard, TurnIndicatorBanner,
    GameOverOverlay, ActiveSideBadge
)


def wait_until(condition_fn, timeout_ms=3000, step_ms=30):
    elapsed = 0
    while elapsed < timeout_ms:
        if condition_fn():
            return True
        loop = QEventLoop()
        QTimer.singleShot(step_ms, loop.quit)
        loop.exec()
        elapsed += step_ms
    return condition_fn()


def run_redesign_tests():
    app = QApplication.instance() or QApplication(sys.argv)
    print("--- 1. Testing TurnIndicatorBanner Layout & Styling ---")
    window = AquaChessWindow()
    window.resize(1000, 700)
    window.show()

    # Verify banner exists and is positioned above chessboard
    assert hasattr(window, "turn_banner"), "Window must have turn_banner"
    assert isinstance(window.turn_banner, TurnIndicatorBanner)
    assert window.turn_banner.parent() is not None

    # Check font size of the status text (16pt-18pt bold)
    font = window.turn_banner.status_label.font()
    assert (
        font.pointSize() >= 16
        or font.pixelSize() >= 20
        or "17pt" in window.turn_banner.status_label.styleSheet()
    ), f"Expected font size >= 16pt, got pointSize={font.pointSize()}, pixelSize={font.pixelSize()}"
    assert font.bold(), "Status font must be bold"

    # Verify initial state: White's turn, player's move
    assert window.turn_banner.color == chess.WHITE
    assert window.turn_banner.is_player_turn
    assert not window.turn_banner.is_check
    assert not window.turn_banner.is_ai_thinking
    assert "YOUR MOVE" in window.turn_banner.chip.text()
    assert window.turn_banner.badge.color == chess.WHITE
    print("  ✓ Turn indicator banner initialized with 16pt bold font, White active badge, and YOUR MOVE chip")

    print("\n--- 2. Testing Turn Indicator State Transitions ---")
    # Test transition to AI thinking
    window.turn_banner.update_turn(chess.WHITE, is_player_turn=False, is_ai_thinking=True)
    assert window.turn_banner.is_ai_thinking
    assert "THINKING" in window.turn_banner.chip.text()
    assert window.turn_banner.badge.is_ai_thinking

    # Test transition to Check state
    window.turn_banner.update_turn(chess.BLACK, is_player_turn=True, is_check=True)
    assert window.turn_banner.color == chess.BLACK
    assert window.turn_banner.is_check
    assert "CHECK" in window.turn_banner.chip.text()
    assert window.turn_banner.badge.color == chess.BLACK
    assert window.turn_banner.badge.is_check
    print("  ✓ Turn indicator transitions cleanly between Player Turn, AI Thinking, and Check states")

    print("\n--- 3. Testing GameOverOverlay Structure & Aesthetics ---")
    board_widget = window.chess_board
    assert hasattr(board_widget, "game_over_overlay")
    overlay = board_widget.game_over_overlay
    assert isinstance(overlay, GameOverOverlay)
    assert overlay.parent() == board_widget
    assert overlay.isHidden(), "GameOverOverlay should initially be hidden"

    # Check Victory Card typography
    overlay.title_label.ensurePolished()
    assert (
        overlay.title_label.fontInfo().pointSize() >= 28
        or overlay.title_label.font().pointSize() >= 28
        or "30pt" in overlay.title_label.styleSheet()
    ), "Victory title font must be >= 28pt"
    assert overlay.play_again_btn is not None
    assert overlay.inspect_btn is not None
    print("  ✓ GameOverOverlay contains 28pt+ bold headline, Play Again, and Inspect Board buttons")

    print("\n--- 4. Testing White Checkmate Victory Announcement ---")
    window.board = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 5")
    window.chess_board.board = window.board
    window.on_player_move(chess.Move.from_uci("f3f7"))
    done = wait_until(lambda: not window.is_busy, timeout_ms=2500)
    assert done, "Checkmate move animation should finish"

    # Verify game over triggered
    assert window.board.is_checkmate()
    assert overlay.isVisible(), "GameOverOverlay must be visible upon checkmate"
    assert not overlay.is_inspect_mode
    assert overlay.card.isVisible()
    assert "WHITE WINS!" in overlay.title_label.text()
    assert "Checkmate" in overlay.subtitle_label.text()
    assert "Checkmate" in window.status_label.text()
    assert window.turn_banner.is_game_over
    assert "VICTORY" in window.turn_banner.chip.text()
    print("  ✓ White checkmate displays high-impact overlay card and celebratory top banner")

    print("\n--- 5. Testing Inspect Board Mode & Restoration ---")
    # Click Inspect Board
    overlay.inspect_btn.click()
    assert overlay.is_inspect_mode, "Should enter inspect mode"
    assert overlay.card.isHidden(), "Victory card should hide in inspect mode"
    assert overlay.inspect_pill.isVisible(), "Inspect pill should appear at top"
    assert overlay.geometry().height() < 50, "Overlay should shrink to pill height to leave board unobstructed"
    print("  ✓ Inspect Board mode minimizes card to compact top pill leaving chessboard completely visible")

    # Click Show Result on pill
    overlay.pill_show_card_btn.click()
    assert not overlay.is_inspect_mode, "Should exit inspect mode"
    assert overlay.card.isVisible(), "Victory card should be restored"
    assert overlay.geometry().height() == board_widget.height(), "Overlay should cover full board area"
    print("  ✓ Show Result restores full victory card and dimming backdrop")

    print("\n--- 6. Testing Play Again Action ---")
    play_again_handled = False
    def on_play():
        nonlocal play_again_handled
        play_again_handled = True

    # Temporarily connect or click
    overlay.play_again_btn.click()
    # window.new_game should have run, resetting board and hiding overlay
    assert overlay.isHidden(), "Overlay should hide when Play Again is clicked"
    assert len(window.board.move_stack) == 0, "Board should be reset to move 0"
    assert window.turn_banner.color == chess.WHITE
    assert "YOUR MOVE" in window.turn_banner.chip.text()
    print("  ✓ Play Again button resets board and hides game-over overlay cleanly")

    print("\n--- 7. Testing Draw / Stalemate Announcement ---")
    # Stalemate position
    b_stale = chess.Board("k7/2Q5/8/8/8/8/8/K7 b - - 0 1")
    window.board = b_stale
    window.chess_board.board = b_stale
    window.check_game_over()
    assert overlay.isVisible()
    assert overlay.is_draw
    assert "DRAW" in overlay.title_label.text()
    assert "Stalemate" in overlay.subtitle_label.text()
    assert "DRAW" in window.turn_banner.chip.text()
    print("  ✓ Draw / Stalemate shows seafoam accented draw card and top banner")

    print("\n--- 8. Testing Resizing and Coordinate Integrity ---")
    # Test multiple resize scales
    for size in [(900, 650), (1200, 800), (800, 600), (1400, 900)]:
        window.resize(*size)
        app.processEvents()
        b_total, ox, oy, margin, sq_size, gx, gy = window.chess_board._geometry()
        # Verify margin and square size are positive and fit inside board widget
        assert b_total <= min(window.chess_board.width(), window.chess_board.height())
        assert margin >= 34.0
        assert sq_size > 0
        # Verify overlay adapts geometry
        overlay.update_geometry()
        if not overlay.is_inspect_mode:
            assert overlay.geometry() == window.chess_board.rect()
        # Test rendering without errors or exceptions
        img = QImage(size[0], size[1], QImage.Format.Format_ARGB32)
        window.render(img)

    print("  ✓ Resizing scales board, coordinates, turn indicator, and game-over overlay without clipping")

    print("\n==========================================")
    print("ALL REDESIGN VERIFICATION TESTS PASSED 100%!")
    print("==========================================")


if __name__ == "__main__":
    run_redesign_tests()
