import os
import sys
import math
import pygame
from .config import COLS, ROWS, LEVELS, TILES_DEF
from .engine import GameState
from .solver import astar_solver, is_goal

# ---------------------------------------------------------------------------
# Symbol -> tile image lookup
# ---------------------------------------------------------------------------
SYMBOL_TO_LETTER = {
    "=": "A",
    "◻": "B",
    "+": "C",
    "◊": "D",
    "∗": "E",
    "▷": "F",
    "X": "G",
    "O": "H",
    " ": "BLANK",
}

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
CELL_SIZE = 150
LEFT_MARGIN = 46          # room for the pulsing EXIT arrow beside column 0
TOP_BAR = 64               # HUD strip
BOTTOM_BAR = 92             # buttons + message strip
GRID_W = COLS * CELL_SIZE
GRID_H = ROWS * CELL_SIZE
PLAY_WINDOW = (LEFT_MARGIN + GRID_W, TOP_BAR + GRID_H + BOTTOM_BAR)

MENU_WINDOW = (560, 700)
FPS = 60
AUTO_STEP_DELAY_MS = 550
HINT_DISPLAY_MS = 3500
MESSAGE_DISPLAY_MS = 2600

# Colors
BG = (20, 27, 38)
PANEL = (30, 40, 55)
ACCENT = (245, 200, 66)
GOOD = (90, 200, 130)
BAD = (220, 90, 90)
WALK_HI = (90, 170, 235)
SLIDE_HI = (120, 220, 140)
TEXT = (235, 238, 242)
MUTED = (150, 160, 175)

DIFFICULTY_COLOR = {
    "starter": (90, 200, 130),
    "junior": (240, 175, 70),
    "expert": (220, 90, 90),
}

STATE_MENU, STATE_PLAY, STATE_WIN = range(3)


def difficulty_of(level_name):
    return level_name.split("-")[0]


class Button:
    """A simple clickable rectangle with a label."""

    def __init__(self, rect, label, color=PANEL, text_color=TEXT):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.text_color = text_color

    def draw(self, surf, font, hovered=False):
        color = tuple(min(255, c + 22) for c in self.color) if hovered else self.color
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2, border_radius=8)
        txt = font.render(self.label, True, self.text_color)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)


class GameVisualizer:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.font_title = pygame.font.SysFont("arial", 30, bold=True)
        self.font_big = pygame.font.SysFont("arial", 22, bold=True)
        self.font_med = pygame.font.SysFont("arial", 18)
        self.font_small = pygame.font.SysFont("arial", 14)

        self.screen = pygame.display.set_mode(MENU_WINDOW)
        pygame.display.set_caption("Temple Trap Solver - Interactive")
        self.clock = pygame.time.Clock()

        self.assets = {}
        self.load_assets()

        self.state = STATE_MENU
        self.levels = list(LEVELS.keys())

        # play-state fields
        self.level_name = None
        self.gs = None
        self.move_count = 0
        self.optimal_cost = None
        self.exit_available = False
        self.exit_cost = None

        self.hint_action = None
        self.hint_until = 0

        self.auto_path = None
        self.auto_idx = 0
        self.auto_playing = False
        self.auto_next_tick = 0

        self.message = ""
        self.message_until = 0
        self.win_moves = 0

        self._build_menu_buttons()

    # ------------------------------------------------------------------
    # Asset loading
    # ------------------------------------------------------------------
    def load_assets(self):
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        for letter in ["A", "B", "C", "D", "E", "F", "G", "H"]:
            img_path = os.path.join(assets_dir, f"tile_{letter}.png")
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert_alpha()
                self.assets[letter] = pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
            else:
                surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
                surf.fill((180, 160, 130))
                pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 2)
                self.assets[letter] = surf

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------
    def _build_menu_buttons(self):
        self.menu_buttons = []
        cols = 2
        bw, bh = 240, 60
        gap_x, gap_y = 20, 16
        start_x = (MENU_WINDOW[0] - (cols * bw + (cols - 1) * gap_x)) // 2
        start_y = 130
        for i, name in enumerate(self.levels):
            r, c = divmod(i, cols)
            x = start_x + c * (bw + gap_x)
            y = start_y + r * (bh + gap_y)
            color = DIFFICULTY_COLOR.get(difficulty_of(name), PANEL)
            dim_color = tuple(int(v * 0.35) for v in color)
            self.menu_buttons.append(Button((x, y, bw, bh), name, color=dim_color))

    def draw_menu(self):
        self.screen.fill(BG)
        title = self.font_title.render("Temple Trap - Select a Level", True, TEXT)
        self.screen.blit(title, title.get_rect(center=(MENU_WINDOW[0] // 2, 55)))

        sub = self.font_small.render(
            "Click a level to play. Solve it yourself, ask for a hint, or watch it auto-solve.",
            True, MUTED,
        )
        self.screen.blit(sub, sub.get_rect(center=(MENU_WINDOW[0] // 2, 90)))

        mouse = pygame.mouse.get_pos()
        for btn in self.menu_buttons:
            btn.draw(self.screen, self.font_med, hovered=btn.hit(mouse))

        legend_y = MENU_WINDOW[1] - 46
        x = 40
        for diff, color in DIFFICULTY_COLOR.items():
            pygame.draw.rect(self.screen, color, (x, legend_y, 16, 16), border_radius=3)
            lbl = self.font_small.render(diff.capitalize(), True, MUTED)
            self.screen.blit(lbl, (x + 22, legend_y - 1))
            x += 120

        pygame.display.flip()

    def handle_menu_click(self, pos):
        for btn in self.menu_buttons:
            if btn.hit(pos):
                self.start_level(btn.label)
                return

    # ------------------------------------------------------------------
    # Level lifecycle
    # ------------------------------------------------------------------
    def start_level(self, level_name):
        self.level_name = level_name
        self._reset_state()
        self.screen = pygame.display.set_mode(PLAY_WINDOW)
        pygame.display.set_caption(f"Temple Trap Solver - {level_name}")

        path, cost = astar_solver(self._fresh_gs())
        self.optimal_cost = cost if path else None
        self.state = STATE_PLAY
        self._build_play_buttons()
        self._refresh_goal_status()

    def _fresh_gs(self):
        lvl = LEVELS[self.level_name]
        return GameState(lvl["board"].copy(), lvl["pawn_pos"], "Ground", lvl["orientation"].copy())

    def _reset_state(self):
        self.gs = self._fresh_gs()
        self.move_count = 0
        self.hint_action = None
        self.auto_path = None
        self.auto_playing = False
        self.message = ""
        self._refresh_goal_status()

    def _build_play_buttons(self):
        bw, bh = 96, 40
        gap = 12
        total = 4 * bw + 3 * gap
        start_x = (PLAY_WINDOW[0] - total) // 2
        y = TOP_BAR + GRID_H + (BOTTOM_BAR - bh) // 2 + 14
        labels = ["Restart", "Hint", "Auto-Solve", "Menu"]
        self.play_buttons = {}
        for i, lbl in enumerate(labels):
            x = start_x + i * (bw + gap)
            self.play_buttons[lbl] = Button((x, y, bw, bh), lbl)

    # ------------------------------------------------------------------
    # Core interaction logic
    # ------------------------------------------------------------------
    def _refresh_goal_status(self):
        goal = is_goal(self.gs)
        if goal is not None:
            self.exit_available = True
            self.exit_cost = goal[1]
        else:
            self.exit_available = False
            self.exit_cost = None

    def _set_message(self, text):
        self.message = text
        self.message_until = pygame.time.get_ticks() + MESSAGE_DISPLAY_MS

    def slidable_tiles(self):
        result = set()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nidx = self.gs.neighbor_index(self.gs.blank, dr, dc)
            if nidx is not None and self.gs.can_slide(nidx):
                result.add(nidx)
        return result

    def walkable_destinations(self):
        """Ground-layer standable cells reachable from the pawn (excludes cell 0,
        which is only reached via the dedicated EXIT action)."""
        dest = {}
        dist_map = self.gs.pawn_distances()
        for (idx, layer), cost in dist_map.items():
            if layer != "Ground" or idx == 0:
                continue
            if idx == self.gs.pawn and layer == self.gs.layer:
                continue
            tile = self.gs.tile_at(idx)
            if tile == " " or not TILES_DEF[tile][2]:
                continue
            dest[idx] = cost
        return dest

    def try_slide(self, idx):
        if self.gs.can_slide(idx):
            self.gs.slide(idx)
            self.move_count += 1
            self.hint_action = None
            self._refresh_goal_status()
            return True
        return False

    def try_walk(self, idx):
        dest = self.walkable_destinations()
        if idx in dest:
            self.gs.pawn = idx
            self.gs.layer = "Ground"
            self.move_count += dest[idx]
            self.hint_action = None
            self._refresh_goal_status()
            return True
        return False

    def perform_exit(self):
        goal = is_goal(self.gs)
        if goal is None:
            self._set_message("No exit path from here yet.")
            return
        layer, cost = goal
        self.move_count += cost
        self.win_moves = self.move_count
        self.state = STATE_WIN

    def do_hint(self):
        path, cost = astar_solver(GameState(self.gs.tiles.copy(), self.gs.pawn, self.gs.layer, self.gs.rotations.copy()))
        if not path:
            self._set_message("No solution exists from the current position.")
            return
        self.hint_action = path[0]
        self.hint_until = pygame.time.get_ticks() + HINT_DISPLAY_MS

    def toggle_auto(self):
        if self.auto_playing:
            self.auto_playing = False
            self._set_message("Auto-solve paused.")
            return
        path, cost = astar_solver(GameState(self.gs.tiles.copy(), self.gs.pawn, self.gs.layer, self.gs.rotations.copy()))
        if not path:
            self._set_message("No solution exists from the current position.")
            return
        self.auto_path = path
        self.auto_idx = 0
        self.auto_playing = True
        self.auto_next_tick = pygame.time.get_ticks()
        self._set_message("Auto-solving...")

    def _advance_auto(self):
        action, arg = self.auto_path[self.auto_idx]
        if action == "slide":
            self.gs.slide(arg)
            self.move_count += 1
        elif action == "walk":
            dest_idx, dest_layer, wcost = arg
            self.gs.pawn = dest_idx
            self.gs.layer = dest_layer
            self.move_count += wcost
        self.auto_idx += 1
        self._refresh_goal_status()
        if self.auto_idx >= len(self.auto_path):
            self.auto_playing = False
            self.win_moves = self.move_count
            self.state = STATE_WIN

    # ------------------------------------------------------------------
    # Click routing
    # ------------------------------------------------------------------
    def handle_play_click(self, pos):
        for lbl, btn in self.play_buttons.items():
            if btn.hit(pos):
                self._handle_button(lbl)
                return

        exit_rect = self._exit_rect()
        if self.exit_available and exit_rect.collidepoint(pos):
            self.perform_exit()
            return

        x, y = pos
        if LEFT_MARGIN <= x < LEFT_MARGIN + GRID_W and TOP_BAR <= y < TOP_BAR + GRID_H:
            c = (x - LEFT_MARGIN) // CELL_SIZE
            r = (y - TOP_BAR) // CELL_SIZE
            idx = r * COLS + c

            # A cell can rarely be both a valid slide target and a valid walk
            # destination at once. Default priority is slide; hold SHIFT to
            # force the walk interpretation for that click instead.
            shift_held = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
            first, second = (self.try_walk, self.try_slide) if shift_held else (self.try_slide, self.try_walk)
            if first(idx):
                return
            if second(idx):
                return

    def _handle_button(self, label):
        if label == "Restart":
            self._reset_state()
        elif label == "Hint":
            self.do_hint()
        elif label == "Auto-Solve":
            self.toggle_auto()
        elif label == "Menu":
            self.state = STATE_MENU
            self.screen = pygame.display.set_mode(MENU_WINDOW)
            pygame.display.set_caption("Temple Trap Solver - Interactive")

    def _exit_rect(self):
        row0_y = TOP_BAR
        return pygame.Rect(2, row0_y, LEFT_MARGIN - 6, CELL_SIZE)

    # ------------------------------------------------------------------
    # Drawing: play screen
    # ------------------------------------------------------------------
    def draw_play(self):
        self.screen.fill(BG)
        self._draw_hud()
        self._draw_grid()
        self._draw_exit_arrow()
        self._draw_buttons_and_message()
        pygame.display.flip()

    def _draw_hud(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, PLAY_WINDOW[0], TOP_BAR))
        name_txt = self.font_big.render(self.level_name, True, TEXT)
        self.screen.blit(name_txt, (14, 10))

        opt_str = str(self.optimal_cost) if self.optimal_cost is not None else "?"
        stats = self.font_med.render(f"Moves: {self.move_count}   |   Optimal: {opt_str}", True, MUTED)
        self.screen.blit(stats, (14, 36))

        mode_txt = "AUTO-SOLVING" if self.auto_playing else "Manual"
        mode_color = ACCENT if self.auto_playing else GOOD
        mode_surf = self.font_small.render(mode_txt, True, mode_color)
        self.screen.blit(mode_surf, (PLAY_WINDOW[0] - mode_surf.get_width() - 14, 22))

    def _draw_grid(self):
        slidable = self.slidable_tiles()
        walkable = self.walkable_destinations()

        for idx, tile_symbol in enumerate(self.gs.tiles):
            r, c = divmod(idx, COLS)
            x = LEFT_MARGIN + c * CELL_SIZE
            y = TOP_BAR + r * CELL_SIZE

            if tile_symbol != " ":
                letter = SYMBOL_TO_LETTER[tile_symbol]
                base_img = self.assets[letter]
                rot_deg = -self.gs.rotations[idx] * 90
                rotated_img = pygame.transform.rotate(base_img, rot_deg)
                rect = rotated_img.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                self.screen.blit(rotated_img, rect.topleft)
            else:
                pygame.draw.rect(self.screen, (10, 12, 16), (x, y, CELL_SIZE, CELL_SIZE))

            if idx in slidable and idx in walkable:
                self._draw_overlay(x, y, SLIDE_HI, "SLIDE (shift=WALK)")
            elif idx in slidable:
                self._draw_overlay(x, y, SLIDE_HI, "SLIDE")
            elif idx in walkable:
                self._draw_overlay(x, y, WALK_HI, "WALK")

            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, CELL_SIZE, CELL_SIZE), 1)

        if self.hint_action and pygame.time.get_ticks() < self.hint_until:
            self._draw_hint()

        # pawn
        pr, pc = divmod(self.gs.pawn, COLS)
        px = LEFT_MARGIN + pc * CELL_SIZE + CELL_SIZE // 2
        py = TOP_BAR + pr * CELL_SIZE + CELL_SIZE // 2
        pawn_color = (240, 60, 60) if self.gs.layer == "Ground" else (245, 215, 45)
        pygame.draw.circle(self.screen, pawn_color, (px, py), 20)
        pygame.draw.circle(self.screen, (255, 255, 255), (px, py), 20, 3)

    def _draw_overlay(self, x, y, color, label):
        overlay = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (*color, 70), overlay.get_rect(), border_radius=6)
        pygame.draw.rect(overlay, (*color, 220), overlay.get_rect(), 3, border_radius=6)
        self.screen.blit(overlay, (x, y))
        tag = self.font_small.render(label, True, color)
        self.screen.blit(tag, (x + 6, y + 6))

    def _draw_hint(self):
        action, arg = self.hint_action
        pulse = (math.sin(pygame.time.get_ticks() / 150) + 1) / 2  # 0..1
        alpha = int(120 + pulse * 100)
        if action == "slide":
            idx = arg
        else:
            idx = arg[0]
        r, c = divmod(idx, COLS)
        x = LEFT_MARGIN + c * CELL_SIZE
        y = TOP_BAR + r * CELL_SIZE
        overlay = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (*ACCENT, alpha), overlay.get_rect(), 6, border_radius=6)
        self.screen.blit(overlay, (x, y))
        label = "HINT: slide" if action == "slide" else "HINT: walk"
        tag = self.font_small.render(label, True, ACCENT)
        self.screen.blit(tag, (x + 6, y + CELL_SIZE - 20))

    def _draw_exit_arrow(self):
        rect = self._exit_rect()
        if self.exit_available:
            pulse = (math.sin(pygame.time.get_ticks() / 180) + 1) / 2
            color = tuple(int(GOOD[i] * (0.6 + 0.4 * pulse)) for i in range(3))
            pygame.draw.polygon(
                self.screen, color,
                [(rect.right, rect.centery - 16), (rect.left + 4, rect.centery), (rect.right, rect.centery + 16)],
            )
        else:
            pygame.draw.polygon(
                self.screen, (60, 66, 74),
                [(rect.right, rect.centery - 10), (rect.left + 6, rect.centery), (rect.right, rect.centery + 10)],
            )

    def _draw_buttons_and_message(self):
        mouse = pygame.mouse.get_pos()
        for lbl, btn in self.play_buttons.items():
            active = (lbl == "Auto-Solve" and self.auto_playing)
            color = ACCENT if active else PANEL
            btn.color = color
            btn.text_color = (20, 20, 20) if active else TEXT
            btn.draw(self.screen, self.font_small, hovered=btn.hit(mouse))

        if self.message and pygame.time.get_ticks() < self.message_until:
            msg_surf = self.font_small.render(self.message, True, ACCENT)
            self.screen.blit(msg_surf, (14, TOP_BAR + GRID_H + 6))
        elif self.exit_available:
            hint_surf = self.font_small.render("Exit is reachable -- click the arrow to escape!", True, GOOD)
            self.screen.blit(hint_surf, (14, TOP_BAR + GRID_H + 6))
        else:
            hint_surf = self.font_small.render(
                "Click a green tile to slide, a blue tile to walk the pawn there.", True, MUTED
            )
            self.screen.blit(hint_surf, (14, TOP_BAR + GRID_H + 6))

    # ------------------------------------------------------------------
    # Win screen
    # ------------------------------------------------------------------
    def draw_win(self):
        self.draw_play_frozen_backdrop()
        overlay = pygame.Surface(PLAY_WINDOW, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.font_title.render("Solved!", True, GOOD)
        self.screen.blit(title, title.get_rect(center=(PLAY_WINDOW[0] // 2, 150)))

        opt_str = str(self.optimal_cost) if self.optimal_cost is not None else "?"
        stat = self.font_big.render(f"Your moves: {self.win_moves}", True, TEXT)
        self.screen.blit(stat, stat.get_rect(center=(PLAY_WINDOW[0] // 2, 200)))
        stat2 = self.font_med.render(f"Optimal solution: {opt_str}", True, MUTED)
        self.screen.blit(stat2, stat2.get_rect(center=(PLAY_WINDOW[0] // 2, 230)))

        if self.optimal_cost is not None:
            if self.win_moves <= self.optimal_cost:
                verdict = "Perfect -- optimal path!"
                vcolor = ACCENT
            else:
                verdict = f"+{self.win_moves - self.optimal_cost} moves over optimal"
                vcolor = MUTED
            v_surf = self.font_med.render(verdict, True, vcolor)
            self.screen.blit(v_surf, v_surf.get_rect(center=(PLAY_WINDOW[0] // 2, 260)))

        self.win_buttons = {
            "Retry": Button((PLAY_WINDOW[0] // 2 - 160, 320, 140, 44), "Retry"),
            "Menu": Button((PLAY_WINDOW[0] // 2 + 20, 320, 140, 44), "Menu"),
        }
        mouse = pygame.mouse.get_pos()
        for btn in self.win_buttons.values():
            btn.draw(self.screen, self.font_med, hovered=btn.hit(mouse))

        pygame.display.flip()

    def draw_play_frozen_backdrop(self):
        self.screen.fill(BG)
        self._draw_hud()
        for idx, tile_symbol in enumerate(self.gs.tiles):
            r, c = divmod(idx, COLS)
            x = LEFT_MARGIN + c * CELL_SIZE
            y = TOP_BAR + r * CELL_SIZE
            if tile_symbol != " ":
                letter = SYMBOL_TO_LETTER[tile_symbol]
                base_img = self.assets[letter]
                rot_deg = -self.gs.rotations[idx] * 90
                rotated_img = pygame.transform.rotate(base_img, rot_deg)
                rect = rotated_img.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                self.screen.blit(rotated_img, rect.topleft)
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, CELL_SIZE, CELL_SIZE), 1)

    def handle_win_click(self, pos):
        for lbl, btn in self.win_buttons.items():
            if btn.hit(pos):
                if lbl == "Retry":
                    self._reset_state()
                    self.state = STATE_PLAY
                elif lbl == "Menu":
                    self.state = STATE_MENU
                    self.screen = pygame.display.set_mode(MENU_WINDOW)
                    pygame.display.set_caption("Temple Trap Solver - Interactive")
                return

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self, initial_level=None):
        if initial_level and initial_level in LEVELS:
            self.start_level(initial_level)

        running = True
        while running:
            now = pygame.time.get_ticks()

            if self.state == STATE_PLAY and self.auto_playing and now >= self.auto_next_tick:
                self._advance_auto()
                self.auto_next_tick = now + AUTO_STEP_DELAY_MS

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == STATE_MENU:
                        self.handle_menu_click(event.pos)
                    elif self.state == STATE_PLAY:
                        self.handle_play_click(event.pos)
                    elif self.state == STATE_WIN:
                        self.handle_win_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == STATE_PLAY:
                            self.state = STATE_MENU
                            self.screen = pygame.display.set_mode(MENU_WINDOW)
                        else:
                            running = False
                    elif self.state == STATE_PLAY:
                        if event.key == pygame.K_r:
                            self._reset_state()
                        elif event.key == pygame.K_h:
                            self.do_hint()
                        elif event.key == pygame.K_a:
                            self.toggle_auto()
                        elif event.key == pygame.K_e and self.exit_available:
                            self.perform_exit()

            if self.state == STATE_MENU:
                self.draw_menu()
            elif self.state == STATE_PLAY:
                self.draw_play()
            elif self.state == STATE_WIN:
                self.draw_win()

            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    # Backward-compatible entry point (auto-plays a pre-computed solution)
    def play_solution(self, initial_state, solution_path):
        self.level_name = self.level_name or "custom"
        self.gs = initial_state
        self.optimal_cost = sum(1 if a == "slide" else arg[2] for a, arg in solution_path)
        self.move_count = 0
        self.auto_path = solution_path
        self.auto_idx = 0
        self.auto_playing = True
        self.auto_next_tick = pygame.time.get_ticks()
        self.screen = pygame.display.set_mode(PLAY_WINDOW)
        self._build_play_buttons()
        self._refresh_goal_status()
        self.state = STATE_PLAY
        self.run()
