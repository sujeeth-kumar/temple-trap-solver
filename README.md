# Temple Trap Puzzle Solver & Interactive Visualizer

An elegant, modular Python implementation that solves the **Temple Trap** sliding-block puzzle using the **$A^*$ Search Algorithm**, wrapped in a fully **interactive Pygame GUI** -- pick a level from an on-screen menu, play it yourself with the mouse, ask for hints, or watch the optimal solution auto-play.

---

## Playing It

```bash
pip install -r requirements.txt
python main.py            # opens the level-select menu
python main.py junior-2   # jumps straight into a level
```

Controls once inside a level:

- **Slide a tile** -- click a green-highlighted tile adjacent to the empty slot
- **Walk the pawn** -- click a blue-highlighted reachable cell
- **Disambiguate an overlapping cell** -- hold Shift while clicking to force "walk" instead of "slide"
- **Escape the temple** -- click the pulsing arrow on the left edge once it lights up (or press E)
- **Get a hint** -- click Hint or press H (flashes the next optimal move for a few seconds)
- **Watch it solve itself** -- click Auto-Solve or press A (replays the A* solution move by move; press again to pause)
- **Restart the level** -- click Restart or press R
- **Back to level menu** -- click Menu or press Esc

The HUD tracks your move count against the solver's optimal cost live, and the win screen tells you whether you matched (or exceeded) the optimal path.

---

## 📄 Project Documentation
The complete formal mathematical formulation, layout constraints, rules, and assignment specifications of the puzzle can be viewed directly in the [Docs Folder](https://github.com/HarshithSubudhi/temple-trap-solver/blob/main/docs/details%20of%20temple%20trap.pdf).

---

## 🧩 The Puzzle & Mechanics Overview

The puzzle is modeled as a $3 \times 3$ grid containing 8 unique sliding tile blocks (labeled A through H) and exactly one empty grid space `""`. The objective is to navigate an explorer pawn from its initial starting block safe-haven to the ultimate escape exit located explicitly on the **left boundary of Cell 0**.

### Core Constraints & Features Implemented:
* **Two-Layer Elevation Architecture:** The game state distinguishes seamlessly between a **Ground** floor and a **Top** corridor layer.
* **Stairs & Vertical Traversal:** Elevation transitions occur dynamically only when the pawn passes through specific tile paths containing staircases (Tiles D and E).
* **The Lock Rule:** A tile containing a hole can slide into the empty spot if and only if the pawn is *not* currently occupying that specific tile.
* **Algorithmic Path Optimization:** Individual block slides cost `1`, and each single-cell node pawn walk step costs `1`. The program calculates the minimal cumulative cost path.

---

## 📝 Algorithmic Implementation Details

### 1. State Space Representation
The game configuration is tracked dynamically using a dedicated state machine layout:
* **Board Matrix:** Represented as a flat list of 9 elements mapping the $3 \times 3$ grid in row-major order (`0` to `8`).
* **Rotational Constraints:** An array tracking orientation offsets (`0`, `1`, `2`, `3`) corresponding to a clockwise transformation from its base identification mark.
* **Pawn State Space:** Tracks both the tile index position (`0` to `8`) and an elevation layer string status (`Ground` or `Top`).

### 2. Action Space & Connectivity
* **Slide Actions (Cost = 1):** Moves a non-pawn occupied tile orthogonally into the empty grid spot `""`.
* **Walk Actions (Cost = 1 per step):** Explores all valid pathway links across matching open tile sides using a Breadth-First Search (BFS) grid computation.
* **Vertical Layer Escalation:** Modifies layer state bounds securely when moving into corridor stair spaces (Tiles D and E).

### 3. Heuristic Function
To optimize node selection and accelerate path discovery within the $A^*$ search queue, the solver uses **Manhattan Distance** tracking:

$$h(n) = |r_{\text{pawn}} - 0| + |c_{\text{pawn}} - 0|$$

This computes the absolute geometric steps required for the pawn to transition from its current grid coordinate $(r, c)$ straight to the target escape exit cell at index `0`. By combining this heuristic estimate with the true accumulated step cost $g(n)$, the solver evaluates the ideal path profile using $f(n) = g(n) + h(n)$.

---

## 📁 Repository Structure

```text
temple-trap-solver/
│
├── temple_trap/              # Main Core Package Modules
│   ├── assets/               # Tight-cropped custom tile images (A-H)
│   ├── __init__.py           # Package namespace initialization
│   ├── config.py             # Map definitions, tiles layouts, & configurations
│   ├── engine.py             # Physical game rules & connectivity mechanics
│   ├── solver.py             # Heuristic functions & A* state space tracking
│   └── visualizer.py         # Pygame window canvas rendering pipeline
│
├── docs/                     # Assignment Specifications
│   └── details_of_temple_trap.pdf
│
├── main.py                   # Launches the interactive GUI (menu-first, or `python main.py <level>`)
└── requirements.txt          # Package framework dependency file
