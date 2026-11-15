# 🌊 Aqua Chess ♟️

A desktop chess application featuring a custom-built Python chess engine and an immersive beach and ocean-inspired interface.

## ✨ Features

- **Human vs. AI** – Play chess against a custom-built chess engine.
- **Three Difficulty Levels**
  - 🏖️ Beach Breeze – Easy
  - 🌊 High Tide – Medium
  - 🌪️ Tsunami – Hard
- **Custom Chess Engine** – Negamax, Alpha-Beta Pruning, Iterative Deepening, and Quiescence Search.
- **Custom SVG Pieces** – Twelve individually designed chess pieces.
- **Coastal UI** – Beach-inspired colors, visual effects, and a glassmorphism dashboard.
- **Live Evaluation** – Position evaluation and captured-piece tracking.
- **Responsive Interface** – Background AI calculations using Qt threading.
- **Self-contained Design** – No external chess engine binaries, image assets, or sound files.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core programming language |
| PySide6 | Desktop GUI framework |
| python-chess | Chess logic and move validation |
| Qt (QThread, Signals & Slots) | Multithreading and UI responsiveness |
| SVG / QPainter | Custom graphics and rendering |

## 🧠 AI Engine

A custom chess engine implemented in pure Python, featuring:

- Negamax with Alpha-Beta Pruning
- Iterative Deepening
- Quiescence Search
- MVV-LVA Move Ordering
- Killer Move Heuristics
- Piece-Square Tables
- Zobrist Hashing and Transposition Table

## 🚀 Installation & Setup

**1. Clone the repository**

```bash
git clone https://github.com/mashail7/Mini_Projects.git
cd Mini_Projects/Aqua-Chess
```

**2. Create a virtual environment**

```bash
python -m venv .venv
```

**3. Activate the environment**

Windows:

```bash
.venv\Scripts\activate
```

**4. Install dependencies**

```bash
pip install -r requirements.txt
```

**5. Run the application**

```bash
run.bat
```

## 🎨 Design Philosophy

Aqua Chess combines traditional chess gameplay with a relaxing coastal atmosphere.

The visual identity is built around warm beach sand, turquoise lagoon water, seashell ivory, and deep ocean tones.

The goal is to create a lightweight, visually engaging chess experience powered entirely by a custom Python implementation.

---

**Status:** In Development

*Built with Python, creativity, and a passion for chess.*
