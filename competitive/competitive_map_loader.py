from pathlib import Path


class CompetitiveMapLoader:
    """Đọc bản đồ Sokoban dành cho hai agent."""

    VALID_SYMBOLS = {"%", "1", "2", "B", "D", "C", " "}

    def __init__(self, file_path):
        self.file_path = Path(file_path)

        self.grid = []
        self.rows = 0
        self.cols = 0

        self.walls = set()
        self.floors = set()
        self.boxes = set()
        self.goals = set()

        # Ví dụ: {1: (3, 3), 2: (3, 5)}
        self.agents = {}

        # Quyền sở hữu: 0 = trung lập, 1 hoặc 2 = agent sở hữu.
        self.box_owners = {}

        self._load()

    @property
    def agent_1(self):
        return self.agents[1]

    @property
    def agent_2(self):
        return self.agents[2]

    def _load(self):
        if not self.file_path.is_file():
            raise FileNotFoundError(
                f"Không tìm thấy file bản đồ: {self.file_path}"
            )

        content = self.file_path.read_text(encoding="utf-8-sig")

        # Giữ nguyên khoảng trắng của bản đồ.
        self.grid = content.splitlines()

        if not self.grid or not any(self.grid):
            raise ValueError("File bản đồ rỗng.")

        self.rows = len(self.grid)
        self.cols = len(self.grid[0])

        for row, line in enumerate(self.grid):
            if len(line) != self.cols:
                raise ValueError(
                    f"Dòng {row + 1} có {len(line)} ký tự, "
                    f"nhưng cần {self.cols} ký tự."
                )

            for col, symbol in enumerate(line):
                position = (row, col)

                if symbol not in self.VALID_SYMBOLS:
                    raise ValueError(
                        f"Ký hiệu không hợp lệ {symbol!r} "
                        f"tại dòng {row + 1}, cột {col + 1}."
                    )

                if symbol == "%":
                    self.walls.add(position)
                    continue

                self.floors.add(position)

                if symbol in ("1", "2"):
                    agent_id = int(symbol)

                    if agent_id in self.agents:
                        raise ValueError(
                            f"Agent {agent_id} xuất hiện nhiều hơn một lần."
                        )

                    self.agents[agent_id] = position

                elif symbol == "B":
                    self.boxes.add(position)

                elif symbol == "D":
                    self.goals.add(position)

                elif symbol == "C":
                    self.boxes.add(position)
                    self.goals.add(position)

        if set(self.agents) != {1, 2}:
            raise ValueError(
                "Bản đồ phải có đúng một agent 1 và một agent 2."
            )

        if not self.boxes:
            raise ValueError("Bản đồ phải có ít nhất một thùng.")

        # Quy ước cho bộ bản đồ của chương trình.
        if len(self.boxes) != len(self.goals):
            raise ValueError(
                f"Số thùng ({len(self.boxes)}) "
                f"khác số đích ({len(self.goals)})."
            )

        # Mọi thùng đều trung lập ở thời điểm bắt đầu.
        self.box_owners = {
            position: 0
            for position in self.boxes
        }

    def is_floor(self, position):
        """Kiểm tra ô nền, chưa xét agent hoặc thùng."""
        return position in self.floors

    def display(self):
        for line in self.grid:
            print(line)