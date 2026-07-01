# main.py
#
# Temple Trap Solver -- Interactive Edition
#
# Launches a Pygame GUI where you can:
#   * pick any of the 12 levels from an on-screen menu
#   * play manually by clicking tiles (slide) or reachable cells (walk)
#   * ask for a Hint (H) that flashes the next optimal move
#   * hit Auto-Solve (A) to watch the A* solution play itself out
#   * escape through the pulsing exit arrow once it's reachable
#
# Run with no arguments to start at the level menu:
#     python main.py
#
# Or jump straight into a specific level (still fully interactive):
#     python main.py junior-2

import sys
from temple_trap.config import LEVELS
from temple_trap.visualizer import GameVisualizer


def main():
    initial_level = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        available = list(LEVELS.keys())
        if arg.isdigit() and 1 <= int(arg) <= len(available):
            initial_level = available[int(arg) - 1]
        elif arg in LEVELS:
            initial_level = arg
        else:
            print(f"Note: '{arg}' is not a known level, starting at the menu instead.")

    viz = GameVisualizer()
    viz.run(initial_level)


if __name__ == "__main__":
    main()
