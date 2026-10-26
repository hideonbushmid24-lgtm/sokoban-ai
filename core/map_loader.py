from pathlib import Path


class MapLoader:
    """Đọc bản đồ Sokoban theo ký hiệu %, A, B, D, C."""

    VALID_SYMBOLS = {"%", "A", "B", "D", "C", " "}

    def __init__(self, file_path):
        self.file_path = Path(file_path)

        # Dữ liệu bản đồ
        self.grid = []
        self.rows = 0
        self.cols = 0

        # Tọa độ được lưu dưới dạng (hàng, cột), bắt đầu từ 0.
        self.walls = set()
        self.floors = set()
        self.boxes = set()
        self.goals = set()
        self.player = None

        self._load()

    def _load(self):
        if not self.file_path.is_file():
            raise FileNotFoundError(
                f"Không tìm thấy file bản đồ: {self.file_path}"
            )

        # utf-8-sig đọc được cả UTF-8 thường và UTF-8 có BOM.
        content = self.file_path.read_text(encoding="utf-8-sig")

        # Giữ nguyên dấu cách vì chúng biểu diễn ô trống.
        self.grid = content.splitlines()

        if not self.grid or not any(self.grid):
            raise ValueError("File bản đồ rỗng.")

        self.rows = len(self.grid)
        self.cols = len(self.grid[0])

        player_count = 0

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

                # Mọi ô không phải tường đều thuộc nền có thể đi.
                # Ô có thùng sẽ bị chặn động trong state.py.
                self.floors.add(position)

                if symbol == "A":
                    self.player = position
                    player_count += 1

                elif symbol == "B":
                    self.boxes.add(position)

                elif symbol == "D":
                    self.goals.add(position)

                elif symbol == "C":
                    # C vừa là thùng, vừa là đích.
                    self.boxes.add(position)
                    self.goals.add(position)

        if player_count != 1:
            raise ValueError(
                f"Bản đồ phải có đúng 1 agent A, "
                f"nhưng tìm thấy {player_count}."
            )

        if not self.boxes:
            raise ValueError("Bản đồ phải có ít nhất 1 thùng.")

        # Quy ước cho bộ bản đồ của đồ án: số thùng bằng số đích.
        if len(self.boxes) != len(self.goals):
            raise ValueError(
                f"Số thùng ({len(self.boxes)}) "
                f"khác số đích ({len(self.goals)})."
            )

    def is_floor(self, position):
        """Kiểm tra ô nền hợp lệ, chưa xét thùng hoặc agent."""
        return position in self.floors

    def display(self):
        """In bố cục ban đầu đọc từ file."""
        for line in self.grid:
            print(line)