"""
engine.py – Pure-Python chess AI for Aqua Chess.

Uses the python-chess library for board representation and move generation.
Implements negamax with alpha-beta pruning, iterative deepening, transposition
tables, quiescence search, null-move pruning, killer moves, and PeSTO-style
piece-square tables with middlegame/endgame interpolation.
"""

import chess
import chess.polyglot
import time
import random

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MATE_SCORE = 100_000
INF = 999_999

# Transposition table flags
FLAG_EXACT = 0
FLAG_ALPHA = 1  # upper bound (failed low)
FLAG_BETA = 2   # lower bound (failed high)

# Max TT entries (~2^18 = 262144)
TT_MAX_SIZE = 262_144

# ---------------------------------------------------------------------------
# Material values (centipawns)
# ---------------------------------------------------------------------------

PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:   20_000,
}

# Phase weights for game-phase calculation (total = 24)
PHASE_WEIGHTS = {
    chess.PAWN:   0,
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK:   2,
    chess.QUEEN:  4,
    chess.KING:   0,
}
TOTAL_PHASE = 24  # 4*1 + 4*1 + 4*2 + 2*4

# ---------------------------------------------------------------------------
# Piece-Square Tables (PeSTO / Simplified Evaluation)
# From White's perspective, a1=index 0, h8=index 63.
# Rank 1 is indices 0-7, rank 8 is indices 56-63.
# ---------------------------------------------------------------------------

# fmt: off

# ---- PAWNS ----
PST_PAWN_MG = [
      0,   0,   0,   0,   0,   0,   0,   0,
     98, 134,  61,  95,  68, 126,  34, -11,
     -6,   7,  26,  31,  65,  56,  25, -20,
    -14,  13,   6,  21,  23,  12,  17, -23,
    -27,  -2,  -5,  12,  17,   6,  10, -25,
    -26,  -4,  -4, -10,   3,   3,  33, -12,
    -35,  -1, -20, -23, -15,  24,  38, -22,
      0,   0,   0,   0,   0,   0,   0,   0,
]

PST_PAWN_EG = [
      0,   0,   0,   0,   0,   0,   0,   0,
    178, 173, 158, 134, 147, 132, 165, 187,
     94, 100,  85,  67,  56,  53,  82,  84,
     32,  24,  13,   5,  -2,   4,  17,  17,
     13,   9,  -3,  -7,  -7,  -8,   3,  -1,
      4,   7,  -6,   1,   0,  -5,  -1,  -8,
     13,   8,   8,  10,  13,   0,   2,  -7,
      0,   0,   0,   0,   0,   0,   0,   0,
]

# ---- KNIGHTS ----
PST_KNIGHT_MG = [
   -167, -89, -34, -49,  61, -97, -15,-107,
    -73, -41,  72,  36,  23,  62,   7, -17,
    -47,  60,  37,  65,  84, 129,  73,  44,
     -9,  17,  19,  53,  37,  69,  18,  22,
    -13,   4,  16,  13,  28,  19,  21,  -8,
    -23,  -9,  12,  10,  19,  17,  25, -16,
    -29, -53, -12,  -3,  -1,  18, -14, -19,
   -105, -21, -58, -33, -17, -28, -19, -23,
]

PST_KNIGHT_EG = [
    -58, -38, -13, -28, -31, -27, -63, -99,
    -25,  -8, -25,  -2,  -9, -25, -24, -52,
    -24, -20,  10,   9,  -1,  -9, -19, -41,
    -17,   3,  22,  22,  22,  11,   8, -18,
    -18,  -6,  16,  25,  16,  17,   4, -18,
    -23,  -3,  -1,  15,  10,  -3, -20, -22,
    -42, -20, -10,  -5,  -2, -20, -23, -44,
    -29, -51, -23, -15, -22, -18, -50, -64,
]

# ---- BISHOPS ----
PST_BISHOP_MG = [
    -29,   4, -82, -37, -25, -42,   7,  -8,
    -26,  16, -18, -13,  30,  59,  18, -47,
    -16,  37,  43,  40,  35,  50,  37,  -2,
     -4,   5,  19,  50,  37,  37,   7,  -2,
     -6,  13,  13,  26,  34,  12,  10,   4,
      0,  15,  15,  15,  14,  27,  18,  10,
      4,  15,  16,   0,   7,  21,  33,   1,
    -33,  -3, -14, -21, -13, -12, -39, -21,
]

PST_BISHOP_EG = [
    -14, -21, -11,  -8,  -7,  -9, -17, -24,
     -8,  -4,   7, -12,  -3, -13,  -4, -14,
      2,  -8,   0,  -1,  -2,   6,   0,   4,
     -3,   9,  12,   9,  14,  10,   3,   2,
     -6,   3,  13,  19,   7,  10,  -3,  -9,
    -12,  -3,   8,  10,  13,   3,  -7, -15,
    -14, -18,  -7,  -1,   4,  -9, -15, -27,
    -23,  -9, -23,  -5,  -9, -16,  -5, -17,
]

# ---- ROOKS ----
PST_ROOK_MG = [
     32,  42,  32,  51,  63,   9,  31,  43,
     27,  32,  58,  62,  80,  67,  26,  44,
     -5,  19,  26,  36,  17,  45,  61,  16,
    -24, -11,   7,  26,  24,  35,  -8, -20,
    -36, -26, -12,  -1,   9,  -7,   6, -23,
    -45, -25, -16, -17,   3,   0,  -5, -33,
    -44, -16, -20,  -9,  -1,  11,  -6, -71,
    -19, -13,   1,  17,  16,   7, -37, -26,
]

PST_ROOK_EG = [
     13,  10,  18,  15,  12,  12,   8,   5,
     11,  13,  13,  11,  -3,   3,   8,   3,
      7,   7,   7,   5,   4,  -3,  -5,  -3,
      4,   3,  13,   1,   2,   1,  -1,   2,
      3,   5,   8,   4,  -5,  -6,  -8, -11,
     -4,   0,  -5,  -1,  -7, -12,  -8, -16,
     -6,  -6,   0,   2,  -9,  -9, -11,  -3,
     -9,   2,   3,  -1,  -5, -13,   4, -20,
]

# ---- QUEENS ----
PST_QUEEN_MG = [
    -28,   0,  29,  12,  59,  44,  43,  45,
    -24, -39,  -5,   1, -16,  57,  28,  54,
    -13, -17,   7,   8,  29,  56,  47,  57,
    -27, -27, -16, -16,  -1,  17,  -2,   1,
     -9, -26,  -9, -10,  -2,  -4,   3,  -3,
    -14,   2, -11,  -2,  -5,   2,  14,   5,
    -35,  -8,  11,   2,   8,  15,  -3,   1,
     -1, -18,  -9,  10, -15, -25, -31, -50,
]

PST_QUEEN_EG = [
     -9,  22,  22,  27,  27,  19,  10,  20,
    -17,  20,  32,  41,  58,  25,  30,   0,
    -20,   6,   9,  49,  47,  35,  19,   9,
      3,  22,  24,  45,  57,  40,  57,  36,
    -18,  28,  19,  47,  31,  34,  39,  23,
    -16, -27,  15,   6,   9,  17,  10,   5,
    -22, -23, -30, -16, -16, -23, -36, -32,
    -33, -28, -22, -43,  -5, -32, -20, -41,
]

# ---- KINGS ----
PST_KING_MG = [
    -65,  23,  16, -15, -56, -34,   2,  13,
     29,  -1, -20,  -7,  -8,  -4, -38, -29,
     -9,  24,   2, -16, -20,   6,  22, -22,
    -17, -20, -12, -27, -30, -25, -14, -36,
    -49,  -1, -27, -39, -46, -44, -33, -51,
    -14, -14, -22, -46, -44, -30, -15, -27,
      1,   7,  -8, -64, -43, -16,   9,   8,
    -15,  36,  12, -54,   8, -28,  24,  14,
]

PST_KING_EG = [
    -74, -35, -18, -18, -11,  15,   4, -17,
    -12,  17,  14,  17,  17,  38,  23,  11,
     10,  17,  23,  15,  20,  45,  44,  13,
     -8,  22,  24,  27,  26,  33,  26,   3,
    -18,  -4,  21,  24,  27,  23,   9, -11,
    -19,  -3,  11,  21,  23,  16,   7,  -9,
    -27, -11,   4,  13,  14,   4,  -5, -17,
    -53, -34, -21, -11, -28, -14, -24, -43,
]

# fmt: on

# Collect PSTs into dicts for easy lookup
PST_MG = {
    chess.PAWN:   PST_PAWN_MG,
    chess.KNIGHT: PST_KNIGHT_MG,
    chess.BISHOP: PST_BISHOP_MG,
    chess.ROOK:   PST_ROOK_MG,
    chess.QUEEN:  PST_QUEEN_MG,
    chess.KING:   PST_KING_MG,
}

PST_EG = {
    chess.PAWN:   PST_PAWN_EG,
    chess.KNIGHT: PST_KNIGHT_EG,
    chess.BISHOP: PST_BISHOP_EG,
    chess.ROOK:   PST_ROOK_EG,
    chess.QUEEN:  PST_QUEEN_EG,
    chess.KING:   PST_KING_EG,
}

# ---------------------------------------------------------------------------
# Passed-pawn masks (precomputed for White; flip squares for Black)
# A pawn on square `sq` is passed if no enemy pawn is on the same or adjacent
# files on ranks ahead. We store bitboard masks per square.
# ---------------------------------------------------------------------------

def _build_passed_pawn_masks():
    """Build passed-pawn detection masks for White pawns."""
    masks = [chess.BB_EMPTY] * 64
    for sq in range(64):
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        mask = chess.BB_EMPTY
        for f in range(max(0, file - 1), min(7, file + 1) + 1):
            for r in range(rank + 1, 8):
                mask |= chess.BB_SQUARES[chess.square(f, r)]
        masks[sq] = mask
    return masks

WHITE_PASSED_MASKS = _build_passed_pawn_masks()


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def _game_phase(board: chess.Board) -> float:
    """
    Return a phase value between 0.0 (endgame) and 1.0 (opening/middlegame).
    Based on remaining non-pawn, non-king material.
    """
    phase = 0
    for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        phase += len(board.pieces(pt, chess.WHITE)) * PHASE_WEIGHTS[pt]
        phase += len(board.pieces(pt, chess.BLACK)) * PHASE_WEIGHTS[pt]
    return min(phase, TOTAL_PHASE) / TOTAL_PHASE


def _pst_score(board: chess.Board):
    """
    Compute middlegame and endgame PST + material scores for both sides.
    Returns (mg_score, eg_score) from White's perspective.
    """
    mg = 0
    eg = 0
    for pt in chess.PIECE_TYPES:
        mg_table = PST_MG[pt]
        eg_table = PST_EG[pt]
        mat = PIECE_VALUES[pt]

        # White pieces
        for sq in board.pieces(pt, chess.WHITE):
            mg += mat + mg_table[sq]
            eg += mat + eg_table[sq]

        # Black pieces – mirror square vertically (rank flip)
        for sq in board.pieces(pt, chess.BLACK):
            mirrored = chess.square_mirror(sq)
            mg -= mat + mg_table[mirrored]
            eg -= mat + eg_table[mirrored]

    return mg, eg


def _bishop_pair_bonus(board: chess.Board) -> int:
    """Return bonus (from White's POV) for having the bishop pair."""
    score = 0
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += 30
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= 30
    return score


def _rook_open_file_bonus(board: chess.Board) -> int:
    """Bonus for rooks on open or semi-open files (from White's POV)."""
    score = 0
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    for sq in board.pieces(chess.ROOK, chess.WHITE):
        file_mask = chess.BB_FILES[chess.square_file(sq)]
        if not (white_pawns & file_mask):
            if not (black_pawns & file_mask):
                score += 20  # fully open
            else:
                score += 10  # semi-open

    for sq in board.pieces(chess.ROOK, chess.BLACK):
        file_mask = chess.BB_FILES[chess.square_file(sq)]
        if not (black_pawns & file_mask):
            if not (white_pawns & file_mask):
                score -= 20
            else:
                score -= 10

    return score


def _passed_pawn_bonus(board: chess.Board) -> int:
    """Bonus for passed pawns (from White's POV)."""
    score = 0
    black_pawns_bb = board.pieces_mask(chess.PAWN, chess.BLACK)
    white_pawns_bb = board.pieces_mask(chess.PAWN, chess.WHITE)

    # White passed pawns
    for sq in board.pieces(chess.PAWN, chess.WHITE):
        if not (WHITE_PASSED_MASKS[sq] & black_pawns_bb):
            rank = chess.square_rank(sq)
            score += 10 + rank * rank * 2  # bigger bonus the further advanced

    # Black passed pawns – mirror to use white masks
    for sq in board.pieces(chess.PAWN, chess.BLACK):
        mirrored = chess.square_mirror(sq)
        if not (WHITE_PASSED_MASKS[mirrored] & white_pawns_bb):
            # "mirrored rank" gives advancement from Black's view
            rank = 7 - chess.square_rank(sq)  # how advanced from Black's side
            score -= 10 + rank * rank * 2

    return score


# ---------------------------------------------------------------------------
# AquaEngine class
# ---------------------------------------------------------------------------

class AquaEngine:
    """
    Pure-Python chess engine for Aqua Chess.

    Features:
      - PeSTO-style evaluation with MG/EG interpolation
      - Negamax with alpha-beta pruning
      - Iterative deepening
      - Transposition table (Zobrist-keyed)
      - Quiescence search with delta pruning
      - Null-move pruning (R=2)
      - Killer move heuristic
      - MVV-LVA move ordering
      - Three difficulty levels
    """

    def __init__(self):
        self.tt: dict[int, tuple[int, int, int, chess.Move | None]] = {}
        # tt entry: {hash: (depth, score, flag, best_move)}
        self.killers: list[list[chess.Move | None]] = [
            [None, None] for _ in range(128)
        ]
        self.nodes = 0
        self.time_limit = 0.0
        self.start_time = 0.0
        self.abort = False
        self._noise = 0  # random noise range (centipawns)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self):
        """Clear transposition table and internal state between games."""
        self.tt.clear()
        self.killers = [[None, None] for _ in range(128)]
        self.nodes = 0
        self.abort = False

    def evaluate(self, board: chess.Board) -> int:
        """
        Public evaluation for the eval bar.
        Returns score in centipawns from White's perspective.
        Positive = White is better.
        """
        return self._evaluate_white(board)

    def find_best_move(
        self, board: chess.Board, difficulty: str
    ) -> tuple[chess.Move, int]:
        """
        Find the best move for the current position.

        Args:
            board: current chess.Board position.
            difficulty: one of "Beach Breeze", "High Tide", "Tsunami".

        Returns:
            (best_move, eval_score) where eval_score is in centipawns from
            White's perspective (positive = White better).
        """
        self.nodes = 0
        self.abort = False

        if difficulty == "Beach Breeze":
            return self._search_fixed_depth(board, max_depth=2, noise=15)
        elif difficulty == "High Tide":
            return self._search_fixed_depth(board, max_depth=3, noise=0)
        elif difficulty == "Tsunami":
            return self._search_iterative(board, max_depth=4, time_limit=2.5)
        else:
            # Default to medium
            return self._search_fixed_depth(board, max_depth=3, noise=0)

    # ------------------------------------------------------------------
    # Internal evaluation
    # ------------------------------------------------------------------

    def _evaluate_white(self, board: chess.Board) -> int:
        """Evaluate position from White's perspective."""
        # Checkmate / stalemate
        if board.is_checkmate():
            # The side to move is checkmated
            return -MATE_SCORE if board.turn == chess.WHITE else MATE_SCORE
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        if board.can_claim_draw():
            return 0

        # Material + PST with phase interpolation
        mg, eg = _pst_score(board)
        phase = _game_phase(board)
        score = int(mg * phase + eg * (1.0 - phase))

        # Bonuses
        score += _bishop_pair_bonus(board)
        score += _rook_open_file_bonus(board)
        score += _passed_pawn_bonus(board)

        return score

    def _evaluate_relative(self, board: chess.Board) -> int:
        """
        Evaluate position relative to the side to move.
        Positive = good for side to move.
        """
        score = self._evaluate_white(board)
        if board.turn == chess.BLACK:
            score = -score

        # Add random noise if set (for easier difficulty levels)
        if self._noise:
            score += random.randint(-self._noise, self._noise)

        return score

    # ------------------------------------------------------------------
    # Move ordering
    # ------------------------------------------------------------------

    def order_moves(
        self,
        board: chess.Board,
        tt_move: chess.Move | None = None,
        killers: list[chess.Move | None] | None = None,
    ) -> list[chess.Move]:
        """
        Order moves for alpha-beta search efficiency.

        Priority:
          1. TT best move
          2. Promotions (queen promotion highest)
          3. Captures ordered by MVV-LVA
          4. Killer moves
          5. Quiet moves scored by PST change
        """
        tt_moves = []
        promotions = []
        captures = []
        killer_moves = []
        quiets = []

        for move in board.legal_moves:
            if tt_move and move == tt_move:
                tt_moves.append((1_000_000, move))
                continue

            if move.promotion:
                promo_bonus = 800_000 + (move.promotion * 100)
                if board.is_capture(move):
                    captured = board.piece_type_at(move.to_square)
                    if captured:
                        promo_bonus += PIECE_VALUES.get(captured, 0)
                promotions.append((promo_bonus, move))
                continue

            if board.is_capture(move):
                # MVV-LVA: prioritise capturing high-value pieces with
                # low-value pieces
                captured = board.piece_type_at(move.to_square)
                attacker = board.piece_type_at(move.from_square)
                if captured and attacker:
                    mvv_lva = PIECE_VALUES[captured] * 10 - PIECE_VALUES[attacker]
                elif captured:
                    mvv_lva = PIECE_VALUES[captured] * 10
                else:
                    # en-passant: capturing a pawn
                    mvv_lva = PIECE_VALUES[chess.PAWN] * 10 - PIECE_VALUES.get(
                        board.piece_type_at(move.from_square), 100
                    )
                captures.append((500_000 + mvv_lva, move))
                continue

            # Killer moves
            if killers and (move == killers[0] or move == killers[1]):
                killer_moves.append((400_000, move))
                continue

            # Quiet move scored by PST improvement
            piece_type = board.piece_type_at(move.from_square)
            if piece_type:
                phase = _game_phase(board)
                mg_table = PST_MG[piece_type]
                eg_table = PST_EG[piece_type]
                if board.turn == chess.WHITE:
                    from_sq = move.from_square
                    to_sq = move.to_square
                else:
                    from_sq = chess.square_mirror(move.from_square)
                    to_sq = chess.square_mirror(move.to_square)

                mg_diff = mg_table[to_sq] - mg_table[from_sq]
                eg_diff = eg_table[to_sq] - eg_table[from_sq]
                pst_change = int(mg_diff * phase + eg_diff * (1.0 - phase))
                quiets.append((pst_change, move))
            else:
                quiets.append((0, move))

        # Sort each category descending by score
        tt_moves.sort(key=lambda x: x[0], reverse=True)
        promotions.sort(key=lambda x: x[0], reverse=True)
        captures.sort(key=lambda x: x[0], reverse=True)
        killer_moves.sort(key=lambda x: x[0], reverse=True)
        quiets.sort(key=lambda x: x[0], reverse=True)

        # Concatenate in priority order
        ordered = []
        for group in [tt_moves, promotions, captures, killer_moves, quiets]:
            for _, move in group:
                ordered.append(move)

        return ordered

    # ------------------------------------------------------------------
    # Quiescence search
    # ------------------------------------------------------------------

    def _quiescence(
        self, board: chess.Board, alpha: int, beta: int, depth_limit: int = 6
    ) -> int:
        """
        Quiescence search: continue searching captures to avoid horizon effect.
        Uses stand-pat, delta pruning, and MVV-LVA ordered captures.
        """
        self.nodes += 1

        # Check time
        if self.time_limit and (self.nodes & 4095) == 0:
            if time.time() - self.start_time >= self.time_limit:
                self.abort = True
                return 0

        # Stand pat: evaluate the position without making any more captures
        stand_pat = self._evaluate_relative(board)

        if stand_pat >= beta:
            return beta

        # Delta pruning threshold: biggest possible capture gain
        DELTA = PIECE_VALUES[chess.QUEEN]  # 900 cp
        if stand_pat + DELTA < alpha:
            return alpha

        if alpha < stand_pat:
            alpha = stand_pat

        if depth_limit <= 0:
            return alpha

        # Generate and order captures
        capture_moves = []
        for move in board.generate_legal_captures():
            captured = board.piece_type_at(move.to_square)
            attacker = board.piece_type_at(move.from_square)
            if move.promotion:
                score = 900
            elif captured and attacker:
                score = PIECE_VALUES[captured] * 10 - PIECE_VALUES[attacker]
            elif captured:
                score = PIECE_VALUES[captured] * 10
            else:
                score = PIECE_VALUES[chess.PAWN] * 10
            capture_moves.append((score, move))

        capture_moves.sort(key=lambda x: x[0], reverse=True)

        for _, move in capture_moves:
            if self.abort:
                return 0

            # Delta pruning: skip captures that can't raise alpha
            captured_pt = board.piece_type_at(move.to_square)
            if captured_pt and not move.promotion:
                if stand_pat + PIECE_VALUES[captured_pt] + 200 < alpha:
                    continue

            board.push(move)
            score = -self._quiescence(board, -beta, -alpha, depth_limit - 1)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    # ------------------------------------------------------------------
    # Transposition table helpers
    # ------------------------------------------------------------------

    def _tt_probe(
        self, board: chess.Board, depth: int, alpha: int, beta: int
    ) -> tuple[int | None, chess.Move | None]:
        """
        Probe transposition table.
        Returns (score_or_None, tt_best_move).
        score is returned only if the stored entry is usable at this depth.
        """
        key = chess.polyglot.zobrist_hash(board)
        entry = self.tt.get(key)
        if entry is None:
            return None, None

        tt_depth, tt_score, tt_flag, tt_move = entry

        if tt_depth >= depth:
            if tt_flag == FLAG_EXACT:
                return tt_score, tt_move
            elif tt_flag == FLAG_ALPHA and tt_score <= alpha:
                return alpha, tt_move
            elif tt_flag == FLAG_BETA and tt_score >= beta:
                return beta, tt_move

        return None, tt_move  # can still use the move for ordering

    def _tt_store(
        self,
        board: chess.Board,
        depth: int,
        score: int,
        flag: int,
        best_move: chess.Move | None,
    ):
        """Store a position in the transposition table."""
        key = chess.polyglot.zobrist_hash(board)

        # Replacement: always replace if deeper or same depth
        existing = self.tt.get(key)
        if existing is not None:
            if existing[0] > depth:
                return  # don't overwrite deeper entries

        # Evict oldest if table is full
        if len(self.tt) >= TT_MAX_SIZE and key not in self.tt:
            # Remove a random entry to make room
            try:
                victim = next(iter(self.tt))
                del self.tt[victim]
            except StopIteration:
                pass

        self.tt[key] = (depth, score, flag, best_move)

    # ------------------------------------------------------------------
    # Negamax with alpha-beta pruning
    # ------------------------------------------------------------------

    def _negamax(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
        allow_null: bool = True,
    ) -> int:
        """
        Negamax search with alpha-beta pruning, null-move pruning,
        check extensions, killer moves, and transposition table.

        Returns score relative to the side to move.
        """
        self.nodes += 1

        # Time check (every 4096 nodes)
        if self.time_limit and (self.nodes & 4095) == 0:
            if time.time() - self.start_time >= self.time_limit:
                self.abort = True
                return 0

        if self.abort:
            return 0

        # Terminal position detection
        if board.is_checkmate():
            return -MATE_SCORE + ply  # being checkmated, penalize by depth
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        if board.can_claim_draw():
            return 0

        # Check extension: extend search by 1 ply when in check (up to max ply 16)
        in_check = board.is_check()
        if in_check and ply < 16:
            depth += 1

        # Leaf node → quiescence search
        if depth <= 0:
            return self._quiescence(board, alpha, beta)

        # Probe transposition table
        tt_score, tt_move = self._tt_probe(board, depth, alpha, beta)
        if tt_score is not None:
            return tt_score

        # Null-move pruning (R=2)
        # Don't null-move when: in check, at root, PV node (beta-alpha>1),
        # or insufficient material for zugzwang safety
        is_pv = beta - alpha > 1
        if (
            allow_null
            and not in_check
            and not is_pv
            and depth >= 3
            and ply > 0
            and self._has_non_pawn_material(board)
        ):
            board.push(chess.Move.null())
            null_score = -self._negamax(
                board, depth - 1 - 2, -beta, -beta + 1, ply + 1, False
            )
            board.pop()

            if self.abort:
                return 0

            if null_score >= beta:
                return beta

        # Get killer moves for this ply
        ply_killers = self.killers[ply] if ply < 128 else [None, None]

        # Generate and order moves
        moves = self.order_moves(board, tt_move=tt_move, killers=ply_killers)

        if not moves:
            # No legal moves – should have been caught above
            if in_check:
                return -MATE_SCORE + ply
            return 0

        best_score = -INF
        best_move = moves[0]
        flag = FLAG_ALPHA

        for move in moves:
            if self.abort:
                return 0

            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1, True)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score
                flag = FLAG_EXACT
                best_move = move

            if alpha >= beta:
                # Beta cutoff – store killer move if it's a quiet move
                if not board.is_capture(move) and not move.promotion:
                    if ply < 128:
                        if move != self.killers[ply][0]:
                            self.killers[ply][1] = self.killers[ply][0]
                            self.killers[ply][0] = move
                flag = FLAG_BETA
                break

        # Store in TT
        self._tt_store(board, depth, best_score, flag, best_move)

        return best_score

    def _has_non_pawn_material(self, board: chess.Board) -> bool:
        """Check if the side to move has non-pawn, non-king pieces."""
        color = board.turn
        for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            if board.pieces(pt, color):
                return True
        return False

    # ------------------------------------------------------------------
    # Search drivers
    # ------------------------------------------------------------------

    def _search_fixed_depth(
        self, board: chess.Board, max_depth: int, noise: int
    ) -> tuple[chess.Move, int]:
        """
        Search to a fixed depth. Used for "Beach Breeze" and "High Tide".
        """
        self._noise = noise
        self.time_limit = 0.0
        self.start_time = time.time()

        best_move = None
        best_score = -INF

        # Simple negamax at fixed depth
        moves = self.order_moves(board)
        if not moves:
            # No legal moves – game over
            return chess.Move.null(), 0

        for move in moves:
            board.push(move)
            score = -self._negamax(board, max_depth - 1, -INF, INF, 1, True)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

        self._noise = 0  # reset noise

        # Convert score to White's perspective
        eval_white = best_score if board.turn == chess.WHITE else -best_score

        return best_move, eval_white

    def _search_iterative(
        self, board: chess.Board, max_depth: int, time_limit: float
    ) -> tuple[chess.Move, int]:
        """
        Iterative deepening search with time limit. Used for "Tsunami".
        """
        self._noise = 0
        self.time_limit = time_limit
        self.start_time = time.time()
        self.abort = False

        best_move = None
        best_score = -INF

        moves = self.order_moves(board)
        if not moves:
            return chess.Move.null(), 0

        # Iterative deepening from depth 1 to max_depth
        for depth in range(1, max_depth + 1):
            if self.abort:
                break

            current_best_move = None
            current_best_score = -INF
            alpha = -INF
            beta = INF

            # Re-order moves: put previous best move first
            if best_move:
                ordered = [best_move] + [m for m in moves if m != best_move]
            else:
                ordered = moves

            for move in ordered:
                if self.abort:
                    break

                board.push(move)
                score = -self._negamax(
                    board, depth - 1, -beta, -alpha, 1, True
                )
                board.pop()

                if self.abort:
                    break

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move

                if score > alpha:
                    alpha = score

            # Only update best if we completed this depth (or have a result)
            if not self.abort and current_best_move is not None:
                best_move = current_best_move
                best_score = current_best_score
            elif current_best_move is not None and best_move is None:
                # Use partial results if we have nothing better
                best_move = current_best_move
                best_score = current_best_score

        # Fallback: if search was aborted before finding anything, pick first
        if best_move is None:
            best_move = moves[0]
            best_score = 0

        # Convert score to White's perspective
        eval_white = best_score if board.turn == chess.WHITE else -best_score

        return best_move, eval_white
