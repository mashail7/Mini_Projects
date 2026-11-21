# 🌊 Aqua Chess ♟️

A desktop chess application featuring a custom-built Python chess engine and an immersive beach and ocean-inspired interface.

## ✨ Features

- **Human vs. AI** – Play chess against a custom-built chess engine.
- **Three Distinct AI Difficulty Levels**
  - 🌴 **Beach Breeze (Easy)** – Novice & beginner-friendly; makes frequent casual blunders and random candidate moves (~45% random, 55% 1-ply raw material with noise).
  - 🌊 **High Tide (Medium)** – Casual & beatable; Depth 2 Negamax without quiescence, captures hanging pieces but misses multi-ply tactical traps.
  - 🌪️ **Tsunami (Hard)** – Challenging tactical opponent; Depth 3–4 Iterative Deepening Negamax with Alpha-Beta pruning, Quiescence search, and full Piece-Square Tables (PST).
- **Custom Chess Engine** – Negamax, Alpha-Beta Pruning, Iterative Deepening, and Quiescence Search.
- **Custom SVG Pieces** – Twelve individually designed vector chess pieces embedded directly in code.
- **Coastal UI** – Beach-inspired colors, visual effects, and a glassmorphism dashboard.
- **Live Evaluation** – Real-time position evaluation bar and captured-piece tracking.
- **Responsive Interface** – Non-blocking background AI calculations using Qt threading.
- **Self-Contained Design** – Zero external chess engine binaries, image assets, or sound files required.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core programming language |
| PySide6 | Desktop GUI framework |
| python-chess | Chess logic and move validation |
| Qt (`QThread`, `Signals & Slots`) | Multithreading and UI responsiveness |
| SVG / `QPainter` | Custom vector graphics and rendering |

## 🧠 AI Engine

A custom chess engine implemented in pure Python, featuring:

- Negamax with Alpha-Beta Pruning
- Iterative Deepening
- Quiescence Search
- MVV-LVA Move Ordering
- Killer Move Heuristics
- Piece-Square Tables (PST)
- Zobrist Hashing and Transposition Table

## 📁 Project Structure

```text
aqua_chess/
├── main.py            # Application entry point & High-DPI setup
├── engine.py          # Custom Negamax + Alpha-Beta AI engine
├── ui.py              # PySide6 GUI, chessboard widget, and QThread worker
├── assets.py          # Embedded SVG chess pieces and coastal QSS styles
├── run.bat            # One-click automatic setup and launcher (Windows)
└── requirements.txt   # Project dependencies
```

## 🚀 Installation & Quick Start

### Prerequisites
- **Python 3.10+** installed on your system (make sure **"Add Python to PATH"** is checked on Windows).

---

### ⚡ Option 1: One-Click Start (Windows — Recommended)
No manual terminal setup is required! Simply double-click **`run.bat`** inside the `aqua_chess` folder:
1. **First Launch:** `run.bat` automatically detects that `.venv` is missing, creates the isolated virtual environment, and installs all dependencies from `requirements.txt`.
2. **Subsequent Launches:** Instantly starts **Aqua Chess** in background windowless mode (`pythonw.exe`) without any console popups.

---

### 🛠️ Option 2: Manual Terminal Setup (Windows / macOS / Linux)

1. **Clone the repository and navigate to the project folder:**
   ```bash
   git clone https://github.com/mashail7/Mini_Projects.git
   cd Mini_Projects/aqua_chess
   ```

2. **Create and activate a virtual environment:**
   - **Windows:**
     ```bash
     python -m venv .venv
     .venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the game:**
   ```bash
   python main.py
   ```

## 🎨 Design Philosophy

Aqua Chess combines traditional chess gameplay with a relaxing coastal atmosphere.

The visual identity is built around warm beach sand, turquoise lagoon water, seashell ivory, and deep ocean tones.

The goal is to create a lightweight, visually engaging chess experience powered entirely by a custom Python implementation.

---

**Status:** Active / Completed

*Built with Python, creativity, and a passion for chess.*
