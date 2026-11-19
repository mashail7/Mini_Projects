"""
Comprehensive test suite for Aqua Chess movement animations, AI pacing, and synchronization.
"""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
import chess

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer, QEasingCurve
from PySide6.QtGui import QPainter, QImage

from ui import (
    AquaChessWindow, ChessBoard, PieceRendererCache,
    MOVE_ANIM_DURATION_MS, AI_PRE_MOVE_DELAY_MS, AI_POST_MOVE_PAUSE_MS
)


def wait_until(condition_fn, timeout_ms=4000, step_ms=40):
    elapsed = 0
    while elapsed < timeout_ms:
        if condition_fn():
            return True
        loop = QEventLoop()
        QTimer.singleShot(step_ms, loop.quit)
        loop.exec()
        elapsed += step_ms
    return condition_fn()


def run_all_tests():
    app = QApplication.instance() or QApplication(sys.argv)
    print("--- 1. Testing Timing & Animation Constants ---")
    assert 250 <= MOVE_ANIM_DURATION_MS <= 350, f"Move anim duration {MOVE_ANIM_DURATION_MS} out of bounds"
    assert 700 <= AI_PRE_MOVE_DELAY_MS <= 1000, f"AI pre-move delay {AI_PRE_MOVE_DELAY_MS} out of bounds"
    assert 300 <= AI_POST_MOVE_PAUSE_MS <= 500, f"AI post-move pause {AI_POST_MOVE_PAUSE_MS} out of bounds"
    print("  ✓ Constants in correct ranges")

    print("\n--- 2. Testing PieceRendererCache ---")
    for color in (chess.WHITE, chess.BLACK):
        for pt in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING):
            renderer = PieceRendererCache.get(color, pt)
            assert renderer is not None, f"Missing renderer for {color}, {pt}"
            assert renderer.isValid(), f"Renderer invalid for {color}, {pt}"
    print("  ✓ All 12 piece SVG renderers cached and valid")

    print("\n--- 3. Testing Normal Move Animation Setup ---")
    board = chess.Board()
    cb = ChessBoard(board)
    cb.resize(600, 600)
    assert cb.move_anim.duration() == MOVE_ANIM_DURATION_MS
    assert cb.move_anim.easingCurve().type() == QEasingCurve.Type.InOutCubic

    move_e4 = chess.Move.from_uci("e2e4")
    finished_called = False
    def on_fin():
        nonlocal finished_called
        finished_called = True

    cb.animate_and_push_move(move_e4, on_finished=on_fin)
    assert cb.is_animating, "Should be animating"
    assert len(cb.anim_moving_pieces) == 1, "Should have 1 moving piece"
    assert cb.anim_moving_pieces[0][1] == chess.E2
    assert cb.anim_moving_pieces[0][2] == chess.E4
    assert cb.anim_target_squares == {chess.E4}
    assert cb.anim_captured_info is None
    assert board.piece_at(chess.E4).piece_type == chess.PAWN
    print("  ✓ Normal move animation setup verified")

    # Test painting while animating
    img = QImage(600, 600, QImage.Format.Format_ARGB32)
    p = QPainter(img)
    cb.anim_progress = 0.5
    cb.paintEvent(None)
    p.end()
    print("  ✓ PaintEvent during flight (mid-progress) rendered successfully")

    cb.reset_animation()
    assert not cb.is_animating
    assert cb.anim_progress == 0.0
    print("  ✓ Reset animation works cleanly")

    print("\n--- 4. Testing Capture Move Animation ---")
    b_cap = chess.Board("rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
    cb_cap = ChessBoard(b_cap)
    cb_cap.resize(600, 600)
    move_exd5 = chess.Move.from_uci("e4d5")
    cb_cap.animate_and_push_move(move_exd5)
    assert cb_cap.is_animating
    assert cb_cap.anim_captured_info is not None
    cap_piece, cap_sq = cb_cap.anim_captured_info
    assert cap_piece.piece_type == chess.PAWN
    assert cap_piece.color == chess.BLACK
    assert cap_sq == chess.D5

    # Test paintEvent at different progress levels for capture dissolve
    for prog in [0.0, 0.5, 0.75, 0.95, 1.0]:
        cb_cap.anim_progress = prog
        img = QImage(600, 600, QImage.Format.Format_ARGB32)
        p = QPainter(img)
        cb_cap.paintEvent(None)
        p.end()
    print("  ✓ Capture piece dissolve levels (0.0 to 1.0) painted successfully")

    print("\n--- 5. Testing Castling Animations ---")
    # White Kingside
    b_wk = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    cb_wk = ChessBoard(b_wk)
    cb_wk.animate_and_push_move(chess.Move.from_uci("e1g1"))
    assert len(cb_wk.anim_moving_pieces) == 2
    king_anim = cb_wk.anim_moving_pieces[0]
    rook_anim = cb_wk.anim_moving_pieces[1]
    assert king_anim[0].piece_type == chess.KING and king_anim[1] == chess.E1 and king_anim[2] == chess.G1
    assert rook_anim[0].piece_type == chess.ROOK and rook_anim[1] == chess.H1 and rook_anim[2] == chess.F1
    assert cb_wk.anim_target_squares == {chess.G1, chess.F1}
    print("  ✓ White Kingside Castling animates both King and Rook")

    # White Queenside
    b_wq = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    cb_wq = ChessBoard(b_wq)
    cb_wq.animate_and_push_move(chess.Move.from_uci("e1c1"))
    assert len(cb_wq.anim_moving_pieces) == 2
    king_anim = cb_wq.anim_moving_pieces[0]
    rook_anim = cb_wq.anim_moving_pieces[1]
    assert king_anim[0].piece_type == chess.KING and king_anim[1] == chess.E1 and king_anim[2] == chess.C1
    assert rook_anim[0].piece_type == chess.ROOK and rook_anim[1] == chess.A1 and rook_anim[2] == chess.D1
    assert cb_wq.anim_target_squares == {chess.C1, chess.D1}
    print("  ✓ White Queenside Castling animates both King and Rook")

    # Black Kingside
    b_bk = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    cb_bk = ChessBoard(b_bk)
    cb_bk.animate_and_push_move(chess.Move.from_uci("e8g8"))
    assert len(cb_bk.anim_moving_pieces) == 2
    king_anim = cb_bk.anim_moving_pieces[0]
    rook_anim = cb_bk.anim_moving_pieces[1]
    assert king_anim[0].piece_type == chess.KING and king_anim[1] == chess.E8 and king_anim[2] == chess.G8
    assert rook_anim[0].piece_type == chess.ROOK and rook_anim[1] == chess.H8 and rook_anim[2] == chess.F8
    print("  ✓ Black Kingside Castling animates both King and Rook")

    # Black Queenside
    b_bq = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
    cb_bq = ChessBoard(b_bq)
    cb_bq.animate_and_push_move(chess.Move.from_uci("e8c8"))
    assert len(cb_bq.anim_moving_pieces) == 2
    king_anim = cb_bq.anim_moving_pieces[0]
    rook_anim = cb_bq.anim_moving_pieces[1]
    assert king_anim[0].piece_type == chess.KING and king_anim[1] == chess.E8 and king_anim[2] == chess.C8
    assert rook_anim[0].piece_type == chess.ROOK and rook_anim[1] == chess.A8 and rook_anim[2] == chess.D8
    print("  ✓ Black Queenside Castling animates both King and Rook")

    print("\n--- 6. Testing En Passant Animation ---")
    b_ep = chess.Board("8/8/8/3Pp3/8/8/8/8 w - e6 0 1")
    cb_ep = ChessBoard(b_ep)
    cb_ep.animate_and_push_move(chess.Move.from_uci("d5e6"))
    assert len(cb_ep.anim_moving_pieces) == 1
    assert cb_ep.anim_moving_pieces[0][1] == chess.D5
    assert cb_ep.anim_moving_pieces[0][2] == chess.E6
    assert cb_ep.anim_captured_info is not None
    ep_piece, ep_sq = cb_ep.anim_captured_info
    assert ep_piece.piece_type == chess.PAWN
    assert ep_sq == chess.E5
    print("  ✓ En Passant animates pawn to e6 and captures e5 pawn cleanly")

    print("\n--- 7. Testing Pawn Promotion Animation ---")
    b_promo = chess.Board("8/4P3/8/8/8/8/8/4K2k w - - 0 1")
    cb_promo = ChessBoard(b_promo)
    m_promo = chess.Move.from_uci("e7e8q")
    cb_promo.animate_and_push_move(m_promo)
    assert cb_promo.is_animating
    assert len(cb_promo.anim_moving_pieces) == 1
    # Moving piece during transit is the pawn
    assert cb_promo.anim_moving_pieces[0][0].piece_type == chess.PAWN
    assert cb_promo.anim_target_squares == {chess.E8}
    # Board state already has promoted queen
    assert b_promo.piece_at(chess.E8).piece_type == chess.QUEEN
    print("  ✓ Promotion animates pawn to 8th rank and promotes cleanly")

    print("\n--- 8. Testing Full Window Game Flow & Synchronization (White) ---")
    window = AquaChessWindow()
    window.resize(900, 650)
    assert not window.is_busy
    assert window.chess_board.interactive
    assert window.board.turn == chess.WHITE

    # 8.1 Human moves e2-e4
    move = chess.Move.from_uci("e2e4")
    window.on_player_move(move)

    # Immediately after human move:
    assert window.is_busy, "Window should be marked busy during animation/AI"
    assert not window.chess_board.interactive, "Chess board should NOT be interactive during move"
    assert not window.undo_btn.isEnabled(), "Undo should be disabled while busy"
    assert window.chess_board.is_animating, "Chess board should be animating human move"
    assert window.ai_worker is not None, "AIWorker should be computing in background without delay"
    print("  ✓ Human move starts animation, locks interactions, and starts AI calculation in parallel")

    # 8.2 Wait for human animation to complete
    anim_done = wait_until(lambda: not window.chess_board.is_animating, timeout_ms=1000)
    assert anim_done, "Human animation should have finished"
    assert window.ai_delay_timer.isActive() or window.ai_delay_elapsed, "AI pre-move delay timer should be active or finished"
    assert window.is_busy, "Window should still be busy (AI thinking)"
    assert not window.chess_board.interactive, "Board still locked during AI thinking"
    print("  ✓ Human animation finishes, moves recorded, AI pre-move presentation delay active")

    # 8.3 Wait for AI pre-move delay and calculation to complete and AI move animation + pause to finish
    fully_restored = wait_until(lambda: not window.is_busy, timeout_ms=5000)
    assert fully_restored, "AI move and pause should finish and restore player control"
    assert window.chess_board.interactive, "Chess board should be interactive again for player"
    assert window.board.turn == chess.WHITE, "Should be White's turn again"
    assert len(window.board.move_stack) == 2, f"Should have 2 moves on board stack, got {len(window.board.move_stack)}"
    assert window.undo_btn.isEnabled(), "Undo button should now be enabled"
    print("  ✓ AI move completed with pause, player turn successfully restored!")

    print("\n--- 9. Testing Rapid Click Guard During Busy State ---")
    window.set_busy_state(True)
    assert not window.chess_board.interactive
    window.undo_move() # Should do nothing
    assert len(window.board.move_stack) == 2, "Undo should be ignored while busy"
    window.set_busy_state(False)
    print("  ✓ Rapid interactions safely blocked during busy state")

    print("\n--- 10. Testing Undo Feature ---")
    assert window.undo_btn.isEnabled()
    window.undo_move()
    assert len(window.board.move_stack) == 0, f"Expected 0 moves after undo, got {len(window.board.move_stack)}"
    assert window.chess_board.last_move is None
    assert not window.undo_btn.isEnabled(), "Undo disabled when no moves left"
    print("  ✓ Undo pops both moves back to player turn cleanly")

    print("\n--- 11. Testing New Game Cancellation ---")
    window.on_player_move(chess.Move.from_uci("e2e4"))
    assert window.is_busy
    window.new_game()
    assert not window.is_busy
    assert window.chess_board.interactive
    assert not window.chess_board.is_animating
    assert not window.ai_delay_timer.isActive()
    assert not window.ai_pause_timer.isActive()
    assert len(window.board.move_stack) == 0
    print("  ✓ New Game cleanly cancels all active timers, animations, and searches")

    print("\n--- 12. Testing Play As Black (AI Opening Move with Pacing) ---")
    window._on_color_changed(1)  # Index 1 = Play as Black
    assert window.player_color == chess.BLACK
    assert window.chess_board.flipped
    assert window.is_busy
    assert not window.chess_board.interactive

    # Wait for AI opening move to complete and pass turn to Black
    black_turn = wait_until(lambda: not window.is_busy, timeout_ms=5000)
    assert black_turn, "AI opening move should complete with animation and pause"
    assert window.board.turn == chess.BLACK
    assert window.chess_board.interactive
    assert len(window.board.move_stack) == 1
    print("  ✓ Play as Black: AI executes opening move with presentation delay & pause, then enables player")

    print("\n--- 13. Testing Checkmate Handling (No AI Response on Game Over) ---")
    # Scholar's mate position: White delivers mate with Qxf7#
    window.player_color = chess.WHITE
    window.chess_board.player_color = chess.WHITE
    window.color_combo.setCurrentIndex(0)
    window.new_game()
    assert not window.is_busy

    b_mate = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 5")
    window.board = b_mate
    window.chess_board.board = b_mate
    m_mate = chess.Move.from_uci("f3f7")
    window.on_player_move(m_mate)
    assert window.is_busy
    # Wait for animation to finish
    mate_done = wait_until(lambda: not window.is_busy, timeout_ms=2000)
    assert mate_done
    assert window.board.is_checkmate()
    assert not window.chess_board.interactive
    assert window.ai_worker is None, "AI should not be triggered when player delivers checkmate"
    assert "Checkmate" in window.status_label.text()
    print("  ✓ Checkmate handled cleanly: animation finishes, status shows Checkmate, AI is not triggered")

    # Cleanup worker before exit to avoid QThread destroyed warning
    if window.ai_worker is not None and window.ai_worker.isRunning():
        window.ai_worker.wait(2000)

    print("\n==========================================")
    print("ALL 13 TEST SUITES PASSED WITH 100% SUCCESS!")
    print("==========================================")

if __name__ == "__main__":
    run_all_tests()
