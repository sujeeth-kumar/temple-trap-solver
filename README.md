# Temple Trap Solver

An interactive Python implementation of the **Temple Trap** sliding-block puzzle featuring an optimal **A\* Search** solver and a **Pygame-based GUI**. Players can solve puzzles manually, request optimal hints, or watch the algorithm automatically solve each level.

---

## Screenshots

### Level Selection

![Level Selection](screenshots/level-selection.png)

### Gameplay

![Gameplay](screenshots/gameplay.png)

### Solution Screen

![Solved](screenshots/solved.png)

---

## Features

- Interactive Pygame graphical interface
- Optimal A* Search algorithm
- Manual puzzle solving
- Hint generation based on the optimal solution
- Auto-solve animation
- Multiple difficulty levels (Starter, Junior, Expert)
- Real-time move counter with optimal solution comparison
- Level selection menu
- Restart and replay support

---

## Tech Stack

- Python 3
- Pygame
- A* Search
- Breadth-First Search (BFS)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/sujeeth-kumar/temple-trap-solver.git
cd temple-trap-solver
```

Install the required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

Launch a specific level directly:

```bash
python main.py junior-2
```

---

## Controls

| Action | Control |
|---------|---------|
| Move Pawn | Click highlighted blue cell |
| Slide Tile | Click highlighted green tile |
| Hint | **H** |
| Auto Solve | **A** |
| Restart Level | **R** |
| Exit Temple | **E** |
| Return to Menu | **Esc** |

---

## Search Algorithm

The puzzle is formulated as a state-space search problem and solved using the **A\*** search algorithm.

Each state consists of:

- Current board configuration
- Tile orientations
- Pawn position
- Current floor (Ground / Top)

Possible actions include:

- Sliding adjacent tiles
- Walking across connected paths
- Transitioning between floors using stair tiles

The A* heuristic efficiently guides the search toward the exit while ensuring an optimal solution.

---

## Project Structure

```text
temple-trap-solver/
│
├── documents/
│   └── templetrap_details.pdf
│
├── screenshots/
│   ├── level-selection.png
│   ├── gameplay.png
│   └── solved.png
│
├── temple_trap/
│   ├── assets/
│   ├── __init__.py
│   ├── config.py
│   ├── engine.py
│   ├── solver.py
│   └── visualizer.py
│
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

---

## Documentation

The repository also includes detailed project documentation describing:

- Problem formulation
- State-space representation
- Action space
- Puzzle rules
- Cost function
- Goal test
- Example puzzle solutions

See:

```
documents/templetrap_details.pdf
```

---

## Future Improvements

- Support additional search algorithms (IDA*, Bidirectional Search)
- Random puzzle generation
- Custom level editor
- Performance benchmarking
- Undo/Redo functionality

---

## Author

**Sujeeth Kumar**

Introduction to Artificial Intelligence coursework project.