from pathlib import Path

import pygame


class CompetitiveGUI:
    BG = (239, 243, 248)
    TEXT = (35, 45, 60)
    BLUE = (45, 115, 215)
    RED = (220, 70, 70)
    BROWN = (170, 115, 65)

    def __init__(self, result, map_name=""):
        self.result = result
        self.states = result["states"]
        self.history = result["history"]

        if (
            not self.states
            or len(self.states) != len(self.history) + 1
        ):
            raise ValueError("Lịch sử trận đấu không hợp lệ.")

        self.map_name = map_name
        self.index = 0
        self.playing = False
        self.interval_ms = 600
        self.last_tick = 0

        self.fonts = {}
        self.buttons = {}

    def _font(self, size):
        if size not in self.fonts:
            self.fonts[size] = pygame.font.Font(
                self.font_path,
                size,
            )

        return self.fonts[size]

    def _text(
        self,
        text,
        x,
        y,
        size=20,
        color=None,
        max_width=None,
    ):
        font = self._font(size)
        text = str(text)

        if (
            max_width is not None
            and font.size(text)[0] > max_width
        ):
            while (
                text
                and font.size(text + "…")[0] > max_width
            ):
                text = text[:-1]

            text += "…"

        image = font.render(
            text,
            True,
            color or self.TEXT,
        )

        self.screen.blit(image, (x, y))

    def _label(self, value, center, size):
        image = self._font(size).render(
            str(value),
            True,
            (255, 255, 255),
        )

        self.screen.blit(
            image,
            image.get_rect(center=center),
        )

    def _draw_board(self, state, area):
        cells = state.floors | state.walls

        rows = max(r for r, _ in cells) + 1
        cols = max(c for _, c in cells) + 1

        cell = max(
            1,
            min(
                area.width // cols,
                area.height // rows,
            ),
        )

        origin_x = area.centerx - cols * cell // 2
        origin_y = area.centery - rows * cell // 2

        def rect_at(position):
            row, col = position

            return pygame.Rect(
                origin_x + col * cell,
                origin_y + row * cell,
                cell,
                cell,
            )

        # Vẽ sàn và tường.
        for position in cells:
            rect = rect_at(position)

            if position in state.walls:
                color = (55, 65, 80)
            else:
                color = (225, 229, 233)

            pygame.draw.rect(
                self.screen,
                color,
                rect,
            )

            pygame.draw.rect(
                self.screen,
                (175, 182, 192),
                rect,
                1,
            )

        # Vẽ đích bằng chấm đỏ.
        for goal in state.goals:
            pygame.draw.circle(
                self.screen,
                self.RED,
                rect_at(goal).center,
                max(1, cell // 9),
            )

        # Vẽ thùng theo quyền sở hữu.
        owners = dict(state.box_owners)

        owner_colors = {
            0: self.BROWN,
            1: self.BLUE,
            2: self.RED,
        }

        for box in state.boxes:
            owner = owners[box]
            color = owner_colors[owner]

            rect = rect_at(box).inflate(
                -cell // 4,
                -cell // 4,
            )

            # Viền vàng giúp nhận biết thùng đang ở đích.
            if box in state.goals:
                pygame.draw.rect(
                    self.screen,
                    (255, 210, 75),
                    rect_at(box),
                    max(1, cell // 15),
                )

            pygame.draw.rect(
                self.screen,
                color,
                rect,
                border_radius=max(0, cell // 12),
            )

            pygame.draw.rect(
                self.screen,
                self.TEXT,
                rect,
                max(1, cell // 25),
                border_radius=max(0, cell // 12),
            )

            if owner and cell >= 20:
                self._label(
                    owner,
                    rect.center,
                    max(12, cell // 3),
                )

        # Agent có hình tròn, thùng có hình vuông.
        agents = (
            (1, state.agent_1, self.BLUE),
            (2, state.agent_2, self.RED),
        )

        for agent_id, position, color in agents:
            center = rect_at(position).center

            pygame.draw.circle(
                self.screen,
                self.TEXT,
                center,
                max(1, cell // 3),
            )

            pygame.draw.circle(
                self.screen,
                color,
                center,
                max(1, cell // 3 - 2),
            )

            if cell >= 20:
                self._label(
                    agent_id,
                    center,
                    max(12, cell // 3),
                )

    def _draw_panel(self, state, panel_x):
        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            (
                panel_x,
                0,
                380,
                self.screen.get_height(),
            ),
        )

        x = panel_x + 24

        self._text("SOKOBAN AI", x, 25, 30)
        self._text("Thi đấu: BFS và GBFS", x, 65, 21)

        self._text(
            self.map_name,
            x,
            95,
            17,
            max_width=330,
        )

        self._text(
            f"Lượt: {state.step_count} | "
            f"Khung: {self.index}/{len(self.history)}",
            x,
            125,
        )

        self._text(
            f"Agent1 - BFS: {state.scores[0]} điểm",
            x,
            160,
            color=self.BLUE,
        )

        self._text(
            f"Agent2 - GBFS: {state.scores[1]} điểm",
            x,
            190,
            color=self.RED,
        )

        if self.index == 0:
            self._text("Trạng thái ban đầu", x, 240)

        else:
            turn = self.history[self.index - 1]

            status_names = {
                "ok": "Hợp lệ",
                "timeout": "Quá giờ",
                "error": "Lỗi agent",
                "startup_error": "Lỗi khởi động",
            }

            for number, key, y in (
                (1, "agent_1", 225),
                (2, "agent_2", 280),
            ):
                decision = turn[key]

                self._text(
                    f"Agent{number}: "
                    f"{decision['action'].value}",
                    x,
                    y,
                )

                status = status_names.get(
                    decision["status"],
                    decision["status"],
                )

                self._text(
                    f"{decision['time_ms']:.3f} ms | {status}",
                    x,
                    y + 28,
                    17,
                )
            conflict = turn.get("conflict")

            if conflict is None:
                self._text(
                    "Xung đột: Không",
                    x,
                    335,
                    16,
                    (100, 110, 120),
                )
            else:
                conflict_names = {
                    "same_position": "Cùng vào một vị trí",
                    "same_box": "Cùng đẩy một thùng",
                }

                conflict_name = conflict_names.get(
                    conflict["type"],
                    conflict["type"],
                )

                self._text(
                    f"Xung đột: {conflict_name}",
                    x,
                    335,
                    16,
                    (190, 110, 35),
                    max_width=330,
                )

                self._text(
                    f"p={conflict['p']:.4f} | "
                    f"Agent{conflict['winner']} thắng, "
                    f"Agent{conflict['loser']} mất lượt",
                    x,
                    357,
                    15,
                    (190, 110, 35),
                    max_width=330,
                )


        if self.index == len(self.history):
            winner_names = {
                0: "Kết thúc: Hai agent hòa nhau",
                1: "Kết thúc: Agent1 thắng",
                2: "Kết thúc: Agent2 thắng",
            }

            status = winner_names[self.result["winner"]]

        else:
            status = (
                "Đang phát lại"
                if self.playing
                else "Đang tạm dừng"
            )

        self._text(
            status,
            x,
            385,
            20,
            (35, 130, 85),
            max_width=330,
        )

        self._text(
            f"Tốc độ phát: {self.interval_ms} ms/lượt",
            x,
            412,
            18,
        )

        # Các nút điều khiển.
        self.buttons = {}

        specs = (
            (
                "play",
                "Tạm dừng" if self.playing else "Chạy",
                x,
                445,
            ),
            ("reset", "Về đầu", x + 172, 445),
            ("prev", "Bước trước", x, 503),
            ("next", "Bước sau", x + 172, 503),
        )

        for key, label, bx, by in specs:
            rect = pygame.Rect(bx, by, 158, 46)

            enabled = not (
                (key == "prev" and self.index == 0)
                or (
                    key == "next"
                    and self.index == len(self.history)
                )
            )

            color = (
                (60, 86, 120)
                if enabled
                else (165, 173, 184)
            )

            pygame.draw.rect(
                self.screen,
                color,
                rect,
                border_radius=7,
            )

            self._label(label, rect.center, 19)
            self.buttons[key] = (rect, enabled)

        self._text("Space: Chạy / Tạm dừng", x, 558, 17)
        self._text("← / →: Lùi / Tiến một lượt", x, 584, 17)
        self._text("↑ / ↓: Nhanh hơn / Chậm hơn", x, 610, 17)
        self._text("R: Về đầu    ESC: Thoát", x, 636, 17)

        self._text(
            "Tròn: Agent | Vuông: Thùng",
            x,
            668,
            17,
        )

        self._text(
            "Nâu: Trung lập | Số: Chủ sở hữu",
            x,
            692,
            16,
        )

    def _control(self, command):
        if command == "play":
            # Nhấn Chạy ở cuối lịch sử sẽ phát lại từ đầu.
            if self.index == len(self.history):
                self.index = 0

            self.playing = (
                not self.playing
                and bool(self.history)
            )

        elif command == "reset":
            self.index = 0
            self.playing = False

        elif command in ("prev", "next"):
            change = -1 if command == "prev" else 1

            self.index = max(
                0,
                min(
                    len(self.history),
                    self.index + change,
                ),
            )

            self.playing = False

        elif command == "faster":
            self.interval_ms = max(
                100,
                self.interval_ms - 100,
            )

        elif command == "slower":
            self.interval_ms = min(
                2000,
                self.interval_ms + 100,
            )

        self.last_tick = pygame.time.get_ticks()

    def run(self):
        pygame.init()

        try:
            self.screen = pygame.display.set_mode(
                (1180, 720),
                pygame.RESIZABLE,
            )

            pygame.display.set_caption(
                "Sokoban AI - Competitive Mode"
            )

            # Ưu tiên font hỗ trợ tiếng Việt.
            candidates = (
                Path("C:/Windows/Fonts/segoeui.ttf"),
                Path("C:/Windows/Fonts/arial.ttf"),
                Path(
                    "/System/Library/Fonts/"
                    "Supplemental/Arial.ttf"
                ),
            )

            self.font_path = next(
                (
                    str(path)
                    for path in candidates
                    if path.is_file()
                ),
                None,
            )

            if self.font_path is None:
                self.font_path = pygame.font.match_font(
                    "dejavusans,arial"
                )

            clock = pygame.time.Clock()
            self.last_tick = pygame.time.get_ticks()
            running = True

            keys = {
                pygame.K_SPACE: "play",
                pygame.K_r: "reset",
                pygame.K_LEFT: "prev",
                pygame.K_RIGHT: "next",
                pygame.K_UP: "faster",
                pygame.K_DOWN: "slower",
            }

            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    elif event.type == pygame.VIDEORESIZE:
                        self.screen = pygame.display.set_mode(
                            (
                                max(960, event.w),
                                max(720, event.h),
                            ),
                            pygame.RESIZABLE,
                        )

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False

                        elif event.key in keys:
                            self._control(keys[event.key])

                    elif (
                        event.type == pygame.MOUSEBUTTONDOWN
                        and event.button == 1
                    ):
                        for command, data in self.buttons.items():
                            rect, enabled = data

                            if (
                                enabled
                                and rect.collidepoint(event.pos)
                            ):
                                self._control(command)
                                break

                if not running:
                    break

                now = pygame.time.get_ticks()

                if (
                    self.playing
                    and now - self.last_tick >= self.interval_ms
                ):
                    self.index = min(
                        len(self.history),
                        self.index + 1,
                    )

                    self.last_tick = now

                    if self.index == len(self.history):
                        self.playing = False

                width, height = self.screen.get_size()
                panel_x = width - 380

                self.screen.fill(self.BG)

                state = self.states[self.index]

                self._draw_board(
                    state,
                    pygame.Rect(
                        20,
                        20,
                        panel_x - 40,
                        height - 40,
                    ),
                )

                self._draw_panel(state, panel_x)

                pygame.display.flip()
                clock.tick(60)

        finally:
            pygame.quit()