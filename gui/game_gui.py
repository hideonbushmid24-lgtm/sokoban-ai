import os
import traceback

from pathlib import Path
from queue import Queue, Empty
from threading import Thread

import pygame

from core.state import State
from search.ucs import UCS
from search.astar import AStar


class GameGUI:
    """GUI Sokoban: chọn thuật toán và phát lại lời giải."""

    BOARD_WIDTH = 740
    PANEL_WIDTH = 360
    HEIGHT = 680
    WIDTH = BOARD_WIDTH + PANEL_WIDTH

    STEP_DELAY_MS = 500

    BACKGROUND_COLOR = (238, 242, 247)
    PANEL_COLOR = (255, 255, 255)

    WALL_COLOR = (55, 65, 81)
    WALL_BORDER = (35, 45, 61)
    FLOOR_COLOR = (226, 226, 226)
    GRID_COLOR = (190, 190, 190)

    GOAL_COLOR = (225, 65, 65)
    BOX_COLOR = (180, 120, 65)
    BOX_ON_GOAL_COLOR = (110, 65, 30)
    BOX_BORDER = (95, 55, 25)

    PLAYER_COLOR = (45, 120, 220)
    PLAYER_BORDER = (25, 65, 140)

    TEXT_COLOR = (35, 40, 48)
    MUTED_COLOR = (110, 115, 125)
    SUCCESS_COLOR = (35, 150, 85)

    BUTTON_COLOR = (58, 91, 135)
    BUTTON_HOVER = (75, 115, 165)
    BUTTON_DISABLED = (170, 175, 185)

    def __init__(self, map_data):
        pygame.init()

        self.map_data = map_data
        self.initial_state = State.from_map_data(map_data)

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT)
        )
        pygame.display.set_caption("Sokoban AI - UCS and A*")

        self.clock = pygame.time.Clock()
        self.running = True

        font_path = self._find_font()

        self.title_font = pygame.font.Font(font_path, 30)
        self.title_font.set_bold(True)

        self.text_font = pygame.font.Font(font_path, 20)
        self.small_font = pygame.font.Font(font_path, 17)

        self.tile_size = max(
            1,
            min(
                64,
                (self.BOARD_WIDTH - 40) // self.map_data.cols,
                (self.HEIGHT - 40) // self.map_data.rows,
            ),
        )

        board_width = self.map_data.cols * self.tile_size
        board_height = self.map_data.rows * self.tile_size

        self.offset_x = (self.BOARD_WIDTH - board_width) // 2
        self.offset_y = (self.HEIGHT - board_height) // 2

        # Dữ liệu tìm kiếm và phát lại lời giải.
        self.algorithm = None
        self.result = None
        self.states = [self.initial_state]
        self.step_index = 0

        self.searching = False
        self.playing = False
        self.error_message = None
        self.last_step_time = 0

        # Luồng tìm kiếm gửi kết quả về luồng giao diện.
        self.result_queue = Queue()

        x = self.BOARD_WIDTH + 24
        button_width = 148
        right_x = x + button_width + 16

        self.buttons = {
            "UCS": pygame.Rect(x, 325, button_width, 42),
            "A*": pygame.Rect(right_x, 325, button_width, 42),
            "play": pygame.Rect(x, 377, button_width, 42),
            "reset": pygame.Rect(right_x, 377, button_width, 42),
            "prev": pygame.Rect(x, 429, button_width, 42),
            "next": pygame.Rect(right_x, 429, button_width, 42),
        }

    @property
    def state(self):
        """Trạng thái đang được hiển thị."""
        return self.states[self.step_index]

    @staticmethod
    def _find_font():
        windows_dir = Path(
            os.environ.get("WINDIR", r"C:\Windows")
        )

        candidates = [
            windows_dir / "Fonts" / "segoeui.ttf",
            windows_dir / "Fonts" / "arial.ttf",
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/Library/Fonts/Arial.ttf"),
        ]

        for path in candidates:
            if path.is_file():
                return str(path)

        for name in [
            "segoeui",
            "arial",
            "dejavusans",
            "liberationsans",
            "notosans",
        ]:
            font_path = pygame.font.match_font(name)

            if font_path:
                return font_path

        raise RuntimeError(
            "Không tìm thấy font hỗ trợ tiếng Việt. "
            "Hãy cài Arial hoặc DejaVu Sans."
        )

    def _has_solution(self):
        return (
            not self.searching
            and self.result is not None
            and self.result["solved"]
        )

    def _start_search(self, algorithm):
        if self.searching:
            return

        self.algorithm = algorithm
        self.result = None
        self.states = [self.initial_state]
        self.step_index = 0

        self.playing = False
        self.searching = True
        self.error_message = None

        solver_class = UCS if algorithm == "UCS" else AStar

        def worker():
            # Luồng này chỉ tìm kiếm, không gọi hàm vẽ Pygame.
            try:
                result = solver_class().solve(self.initial_state)
                self.result_queue.put(("success", result))
            except Exception:
                self.result_queue.put(
                    ("error", traceback.format_exc())
                )

        Thread(target=worker, daemon=True).start()

    def _collect_result(self):
        """Nhận kết quả mà không chặn vòng lặp giao diện."""
        try:
            status, payload = self.result_queue.get_nowait()
        except Empty:
            return

        self.searching = False

        if status == "error":
            self.error_message = "Lỗi tìm kiếm: xem Terminal"
            print(payload)
            return

        self.result = payload

        if self.result["solved"]:
            self.states = self.result["states"]
        else:
            self.states = [self.initial_state]

        self.step_index = 0
        self.playing = False

    def _toggle_play(self):
        if not self._has_solution() or len(self.states) <= 1:
            return

        # Nếu đã phát hết, Space hoặc nút Phát sẽ phát lại từ đầu.
        if self.step_index == len(self.states) - 1:
            self.step_index = 0

        self.playing = not self.playing
        self.last_step_time = pygame.time.get_ticks()

    def _step(self, direction):
        if not self._has_solution():
            return

        # Tiến/lùi thủ công đồng thời tạm dừng phát tự động.
        self.playing = False

        self.step_index = max(
            0,
            min(
                self.step_index + direction,
                len(self.states) - 1,
            ),
        )

    def _reset(self):
        if self.searching:
            return

        # Giữ lời giải đã tìm, đưa phần phát lại về bước 0.
        self.playing = False
        self.step_index = 0

    def _update_playback(self):
        if not self.playing:
            return

        now = pygame.time.get_ticks()

        if now - self.last_step_time >= self.STEP_DELAY_MS:
            self.last_step_time = now

            if self.step_index < len(self.states) - 1:
                self.step_index += 1

            if self.step_index == len(self.states) - 1:
                self.playing = False

    def _button_enabled(self, name):
        if self.searching:
            return False

        if name in ("UCS", "A*"):
            return True

        if not self._has_solution():
            return False

        if name == "play":
            return len(self.states) > 1

        if name == "prev":
            return self.step_index > 0

        if name == "next":
            return self.step_index < len(self.states) - 1

        return True

    def _handle_button(self, name):
        if not self._button_enabled(name):
            return

        if name in ("UCS", "A*"):
            self._start_search(name)
        elif name == "play":
            self._toggle_play()
        elif name == "reset":
            self._reset()
        elif name == "prev":
            self._step(-1)
        elif name == "next":
            self._step(1)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_u:
                    self._start_search("UCS")
                elif event.key == pygame.K_a:
                    self._start_search("A*")
                elif event.key == pygame.K_SPACE:
                    self._toggle_play()
                elif event.key == pygame.K_LEFT:
                    self._step(-1)
                elif event.key == pygame.K_RIGHT:
                    self._step(1)
                elif event.key == pygame.K_r:
                    self._reset()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for name, rect in self.buttons.items():
                        if rect.collidepoint(event.pos):
                            self._handle_button(name)
                            break

    def _cell_rect(self, position):
        row, col = position

        return pygame.Rect(
            self.offset_x + col * self.tile_size,
            self.offset_y + row * self.tile_size,
            self.tile_size,
            self.tile_size,
        )

    def _draw_text(self, text, x, y, font=None, color=None):
        font = font if font is not None else self.text_font
        color = color if color is not None else self.TEXT_COLOR

        available_width = self.WIDTH - x - 20
        displayed_text = text

        if font.size(displayed_text)[0] > available_width:
            while (
                displayed_text
                and font.size(displayed_text + "...")[0]
                > available_width
            ):
                displayed_text = displayed_text[:-1]

            displayed_text += "..."

        surface = font.render(displayed_text, True, color)
        self.screen.blit(surface, (x, y))

    def _draw_board(self):
        state = self.state

        for row in range(self.map_data.rows):
            for col in range(self.map_data.cols):
                position = (row, col)
                rect = self._cell_rect(position)

                if position in state.walls:
                    color = self.WALL_COLOR
                    border = self.WALL_BORDER
                else:
                    color = self.FLOOR_COLOR
                    border = self.GRID_COLOR

                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, border, rect, 1)

        for goal in state.goals:
            rect = self._cell_rect(goal)

            pygame.draw.circle(
                self.screen,
                self.GOAL_COLOR,
                rect.center,
                max(1, self.tile_size // 7),
            )

        for box in state.boxes:
            rect = self._cell_rect(box)
            padding = self.tile_size // 6
            box_rect = rect.inflate(-2 * padding, -2 * padding)

            color = (
                self.BOX_ON_GOAL_COLOR
                if box in state.goals
                else self.BOX_COLOR
            )

            pygame.draw.rect(
                self.screen, color, box_rect, border_radius=5
            )
            pygame.draw.rect(
                self.screen,
                self.BOX_BORDER,
                box_rect,
                width=2,
                border_radius=5,
            )

        player_rect = self._cell_rect(state.player)
        radius = max(1, self.tile_size // 3)

        pygame.draw.circle(
            self.screen,
            self.PLAYER_COLOR,
            player_rect.center,
            radius,
        )
        pygame.draw.circle(
            self.screen,
            self.PLAYER_BORDER,
            player_rect.center,
            radius,
            width=2,
        )

    def _status(self):
        if self.searching:
            return "Đang tìm lời giải...", self.MUTED_COLOR

        if self.error_message:
            return self.error_message, self.GOAL_COLOR

        if self.result is None:
            return "Hãy chọn UCS hoặc A*", self.MUTED_COLOR

        if not self.result["solved"]:
            return "Không có lời giải", self.GOAL_COLOR

        if self.state.is_goal():
            return "Đã hoàn thành", self.SUCCESS_COLOR

        if self.playing:
            return "Đang phát lời giải", self.PLAYER_COLOR

        return "Sẵn sàng / Đang tạm dừng", self.MUTED_COLOR

    def _draw_buttons(self):
        labels = {
            "UCS": "Giải bằng UCS",
            "A*": "Giải bằng A*",
            "play": "Tạm dừng" if self.playing else "Phát lời giải",
            "reset": "Về đầu",
            "prev": "← Bước trước",
            "next": "Bước sau →",
        }

        mouse_position = pygame.mouse.get_pos()

        for name, rect in self.buttons.items():
            if not self._button_enabled(name):
                color = self.BUTTON_DISABLED
            elif rect.collidepoint(mouse_position):
                color = self.BUTTON_HOVER
            else:
                color = self.BUTTON_COLOR

            pygame.draw.rect(
                self.screen, color, rect, border_radius=7
            )

            surface = self.small_font.render(
                labels[name], True, (255, 255, 255)
            )
            self.screen.blit(
                surface,
                surface.get_rect(center=rect.center),
            )

    def _draw_panel(self):
        panel_rect = pygame.Rect(
            self.BOARD_WIDTH, 0, self.PANEL_WIDTH, self.HEIGHT
        )
        pygame.draw.rect(
            self.screen, self.PANEL_COLOR, panel_rect
        )
        pygame.draw.line(
            self.screen,
            self.GRID_COLOR,
            (self.BOARD_WIDTH, 0),
            (self.BOARD_WIDTH, self.HEIGHT),
            2,
        )

        x = self.BOARD_WIDTH + 24

        self._draw_text(
            "SOKOBAN AI", x, 20, font=self.title_font
        )
        self._draw_text(
            "Một agent — UCS và A*",
            x, 63,
            font=self.small_font,
            color=self.MUTED_COLOR,
        )
        self._draw_text(
            self.map_data.file_path.name,
            x, 90,
            font=self.small_font,
        )

        algorithm = self.algorithm or "Chưa chọn"
        self._draw_text(f"Thuật toán: {algorithm}", x, 125)

        if self._has_solution():
            total_steps = len(self.result["actions"])
            steps_text = f"{self.step_index} / {total_steps}"
        else:
            steps_text = "—"

        self._draw_text(f"Số hành động: {steps_text}", x, 155)

        cost_text = "—"
        time_text = "—"
        expanded_text = "—"

        if self.result is not None:
            if self.result["solved"]:
                cost_text = str(self.result["cost"])

            time_text = f"{self.result['time_seconds'] * 1000:.3f} ms"
            expanded_text = str(self.result["nodes_expanded"])

        self._draw_text(f"Tổng chi phí: {cost_text}", x, 185)
        self._draw_text(f"Thời gian giải: {time_text}", x, 215)
        self._draw_text(f"Node mở rộng: {expanded_text}", x, 245)

        status, color = self._status()
        self._draw_text(
            status, x, 283, font=self.small_font, color=color
        )

        self._draw_buttons()

        instructions = [
            "Space: Phát / Tạm dừng",
            "← / →: Lùi / Tiến một bước",
            "U: Giải UCS   |   A: Giải A*",
            "R: Về đầu     |   ESC: Thoát",
            "Mỗi hành động được phát cách nhau 0,5 giây.",
        ]

        for index, text in enumerate(instructions):
            self._draw_text(
                text,
                x,
                495 + index * 28,
                font=self.small_font,
                color=self.MUTED_COLOR,
            )

        completed_boxes = len(self.state.boxes & self.state.goals)

        self._draw_text(
            f"Thùng trên đích: {completed_boxes}/{len(self.state.boxes)}",
            x, 645,
            font=self.small_font,
        )

    def draw(self):
        self.screen.fill(self.BACKGROUND_COLOR)
        self._draw_board()
        self._draw_panel()
        pygame.display.flip()

    def run(self):
        try:
            while self.running:
                self._handle_events()

                if not self.running:
                    break

                self._collect_result()
                self._update_playback()
                self.draw()
                self.clock.tick(60)
        finally:
            pygame.quit()