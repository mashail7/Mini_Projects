"""
Comprehensive test suite verifying the overhauled AI Difficulty System in Aqua Chess:
1. AI Difficulty Modes (Engine Logic):
   - Level 1: Very Easy (Easy) - 45% random legal move, 55% 1-ply raw material + heavy noise [-250, 250]
   - Level 2: Casual / Fairly Easy (Medium) - Depth 2 Negamax without quiescence, moderate noise [-75, 75], top-4 selection
   - Level 3: Challenging (Hard) - Depth 3-4 Negamax + Alpha-Beta + Quiescence + PST + MVV-LVA, 0 noise (deterministic)
   - Resilient parameter handling and backward compatibility for difficulty strings
2. UI Difficulty Selector & Integration:
   - Difficulty dropdown labels with explicit (Easy), (Medium), (Hard) tags
   - Startup default is Easy (index 0)
   - Dynamic mid-game and pre-game difficulty switching immediately updates active AI parameter
   - Difficulty selector enabled when not busy, guarded during AI calculation
   - Asynchronous calculation via AIWorker (QThread)
"""

import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
import time
import random
import chess

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer

from engine import AquaEngine, PIECE_VALUES
from ui import AquaChessWindow, AIWorker, DIFFICULTY_MAP


def wait_until(condition_fn, timeout_ms=4000, step_ms=30):
    elapsed = 0
    while elapsed < timeout_ms:
        if condition_fn():
            return True
        loop = QEventLoop()
        QTimer.singleShot(step_ms, loop.quit)
        loop.exec()
        elapsed += step_ms
    return condition_fn()


def run_difficulty_tests():
    app = QApplication.instance() or QApplication(sys.argv)

    print("--- 1. Testing Difficulty Parameter Aliases & Mappings ---")
    engine = AquaEngine()
    board = chess.Board()

    # Test all variations of difficulty strings
    easy_names = [
        "Beach Breeze (Easy)", "🌴 Beach Breeze (Easy)", "Calmer Waters (Easy)",
        "Easy", "Beach Breeze", "🌴 Beach Breeze"
    ]
    medium_names = [
        "High Tide (Medium)", "🌊 High Tide (Medium)", "Steady Tide (Medium)",
        "Medium", "High Tide", "🌊 High Tide"
    ]
    hard_names = [
        "Tsunami (Hard)", "🌊 Tsunami (Hard)", "Deep Abyss (Hard)",
        "Hard", "Tsunami", "🌊 Tsunami"
    ]

    for name in easy_names:
        m, s = engine.find_best_move(board, name)
        assert m in board.legal_moves, f"Easy move for {name} must be legal"

    for name in medium_names:
        m, s = engine.find_best_move(board, name)
        assert m in board.legal_moves, f"Medium move for {name} must be legal"

    for name in hard_names:
        m, s = engine.find_best_move(board, name)
        assert m in board.legal_moves, f"Hard move for {name} must be legal"

    print("  ✓ All difficulty names, emojis, and parenthetical labels correctly mapped")

    print("\n--- 2. Testing Level 1 — Very Easy (Easy) Engine Logic ---")
    # Position with hanging queen on d4: White to move
    # White has e3xd4 or d1xd4 capturing queen for free (+900 cp raw material)
    hang_queen_board = chess.Board("r1b1k2r/pppp1ppp/8/8/3q4/4P3/PPP2PPP/RNBQKB1R w KQkq - 0 1")

    # Raw material test
    raw_eval_before = engine._evaluate_raw_material(hang_queen_board)
    hang_queen_board.push(chess.Move.from_uci("e3d4"))
    raw_eval_after = engine._evaluate_raw_material(hang_queen_board)
    assert raw_eval_after - raw_eval_before == PIECE_VALUES[chess.QUEEN], (
        f"Capturing queen must improve raw material by 900 cp, got {raw_eval_after - raw_eval_before}"
    )
    hang_queen_board.pop()

    # Easy mode over 100 trials: should exhibit high entropy (~45% random + noise)
    easy_moves = [engine.find_best_move(hang_queen_board, "Beach Breeze (Easy)")[0] for _ in range(100)]
    unique_easy = set(easy_moves)
    # With 35 legal moves, 45% random will produce many unique moves (far more than 5)
    assert len(unique_easy) >= 10, f"Easy should produce high move variety due to 45% random moves; got {len(unique_easy)}"

    # In ~45% of turns, it picks random moves and frequently misses capturing the hanging queen
    queen_captures = sum(1 for m in easy_moves if m.uci() in ("e3d4", "d1d4"))
    blunder_rate = (100 - queen_captures) / 100.0
    assert blunder_rate > 0.25, f"Easy must blunder/miss hanging piece often; blunder rate was {blunder_rate}"
    print(f"  ✓ Level 1 (Easy) exhibits beginner behavior: {len(unique_easy)} distinct moves, missed hanging Queen {blunder_rate*100:.1f}% of the time")

    print("\n--- 3. Testing Level 2 — Casual / Fairly Easy (Medium) Engine Logic ---")
    # In the same hanging queen position, Medium should capture it reliably
    medium_moves = [engine.find_best_move(hang_queen_board, "High Tide (Medium)")[0] for _ in range(25)]
    med_captures = sum(1 for m in medium_moves if m.uci() in ("e3d4", "d1d4"))
    assert med_captures >= 20, f"Medium should capture obvious hanging pieces reliably; got {med_captures}/25"

    # Medium should run quickly (depth 2 with no quiescence search)
    t0 = time.time()
    for _ in range(5):
        engine.find_best_move(board, "High Tide (Medium)")
    med_elapsed = (time.time() - t0) / 5.0
    assert med_elapsed < 0.5, f"Medium search must be fast (<0.5s); took {med_elapsed:.3f}s"
    print(f"  ✓ Level 2 (Medium) plays sensibly: captured hanging Queen {med_captures}/25 times, avg time {med_elapsed*1000:.1f}ms")

    print("\n--- 4. Testing Level 3 — Challenging (Hard) Engine Logic ---")
    # Hard mode must be deterministic (0 noise) and pick the best tactical moves
    hard_move_1, score_1 = engine.find_best_move(hang_queen_board, "Tsunami (Hard)")
    hard_move_2, score_2 = engine.find_best_move(hang_queen_board, "Tsunami (Hard)")
    assert hard_move_1 == hard_move_2, "Hard mode with 0 noise must be deterministic"
    assert hard_move_1.uci() in ("d1d4", "e3d4"), f"Hard mode must capture hanging queen; got {hard_move_1}"

    # Tactical position: Italian/Scotch tactical fork/pin
    tactical_board = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5")
    hard_tactical, _ = engine.find_best_move(tactical_board, "Tsunami (Hard)")
    assert hard_tactical.uci() == "c4d5", f"Hard mode must find tactical move c4d5; got {hard_tactical.uci()}"
    print("  ✓ Level 3 (Hard) plays strong tactical chess (deterministic, found c4d5 and captured queen 100%)")

    print("\n--- 5. Testing UI Difficulty Selector & Labels ---")
    window = AquaChessWindow()
    window.resize(1000, 700)
    window.show()

    assert hasattr(window, "difficulty_combo"), "Window must have difficulty_combo"
    combo = window.difficulty_combo

    # Check item count and labels
    assert combo.count() == 3, f"Difficulty combo should have 3 items; got {combo.count()}"
    labels = [combo.itemText(i) for i in range(combo.count())]
    assert "(Easy)" in labels[0], f"Item 0 must contain (Easy); got {labels[0]}"
    assert "(Medium)" in labels[1], f"Item 1 must contain (Medium); got {labels[1]}"
    assert "(Hard)" in labels[2], f"Item 2 must contain (Hard); got {labels[2]}"

    # Verify default selection on startup is Easy (index 0)
    assert combo.currentIndex() == 0, f"Default selection must be Easy (index 0); got {combo.currentIndex()}"
    assert "(Easy)" in combo.currentText(), f"Default text must contain (Easy); got {combo.currentText()}"
    assert "Easy" in window.active_difficulty, f"Active difficulty should default to Easy; got {window.active_difficulty}"
    print(f"  ✓ Dropdown initialized with labels: {labels}")
    print(f"  ✓ Default selected difficulty on startup is: '{combo.currentText()}' (index 0)")

    print("\n--- 6. Testing Dynamic Mid-Game & Pre-Game Difficulty Switching ---")
    # Change before game
    combo.setCurrentIndex(1)
    assert "(Medium)" in combo.currentText()
    assert "Medium" in window.active_difficulty

    combo.setCurrentIndex(2)
    assert "(Hard)" in combo.currentText()
    assert "Hard" in window.active_difficulty

    combo.setCurrentIndex(0)
    assert "(Easy)" in combo.currentText()
    assert "Easy" in window.active_difficulty

    # Simulate player move and verify active difficulty is used in search
    window.new_game()
    combo.setCurrentIndex(2)  # Switch to Hard mid-game
    assert "Hard" in window.active_difficulty

    board_copy = chess.Board()
    window._start_ai_search(board_copy)
    assert window.ai_worker is not None, "AIWorker should be running"
    assert "Hard" in window.ai_worker.difficulty, f"AIWorker must receive updated Hard difficulty; got {window.ai_worker.difficulty}"

    # Wait for AI worker to finish cleanly
    assert wait_until(lambda: not window.ai_worker.isRunning(), timeout_ms=5000), "AIWorker did not finish in time"
    print("  ✓ Switching difficulty selector immediately updates active AI parameter and worker thread")

    print("\n--- 7. Testing Interaction Lock and Dropdown Guard ---")
    # Verify difficulty combo is enabled when not busy and disabled when busy
    window.set_busy_state(False)
    assert combo.isEnabled(), "Difficulty combo should be enabled during player turn"
    window.set_busy_state(True)
    assert not combo.isEnabled(), "Difficulty combo must be disabled while AI is calculating/busy"
    window.set_busy_state(False)
    assert combo.isEnabled(), "Difficulty combo should be re-enabled after AI turn completes"
    print("  ✓ Difficulty combo state properly guarded by set_busy_state")

    window.close()
    print("\n==========================================")
    print("ALL AI DIFFICULTY TESTS PASSED 100%!")
    print("==========================================")


if __name__ == "__main__":
    run_difficulty_tests()
