from dataclasses import dataclass


# Tọa độ có dạng (hàng, cột).
Position = tuple[int, int]

DIRECTIONS = {
    "North": (-1, 0),
    "East": (0, 1),
    "West": (0, -1),
    "South": (1, 0),
}


@dataclass(frozen=True)
class State:
    """Một trạng thái của trò chơi Sokoban."""

    player: Position
    boxes: frozenset[Position]

    # Thông tin cố định của bản đồ.
    walls: frozenset[Position]
    goals: frozenset[Position]
    floors: frozenset[Position]

    @classmethod
    def from_map_data(cls, map_data):
        """Tạo trạng thái ban đầu từ đối tượng MapLoader."""
        return cls(
            player=map_data.player,
            boxes=frozenset(map_data.boxes),
            walls=frozenset(map_data.walls),
            goals=frozenset(map_data.goals),
            floors=frozenset(map_data.floors),
        )

    def is_goal(self):
        """Hoàn thành khi tất cả thùng đều nằm trên đích."""
        return self.boxes.issubset(self.goals)

    def move(self, action):
        """
        Trả về trạng thái mới nếu hành động hợp lệ.
        Trả về None nếu bị chặn.
        Không thay đổi trạng thái hiện tại.
        """
        if action not in DIRECTIONS:
            raise ValueError(f"Hành động không hợp lệ: {action}")

        dr, dc = DIRECTIONS[action]
        row, col = self.player

        next_position = (row + dr, col + dc)

        # Không được đi vào tường hoặc ra ngoài bản đồ.
        if next_position not in self.floors:
            return None

        new_boxes = self.boxes

        if next_position in self.boxes:
            # Ô mà thùng sẽ được đẩy tới.
            box_destination = (
                next_position[0] + dr,
                next_position[1] + dc,
            )

            # Không đẩy thùng vào tường hoặc ra ngoài bản đồ.
            if box_destination not in self.floors:
                return None

            # Không thể đẩy hai thùng cùng lúc.
            if box_destination in self.boxes:
                return None

            updated_boxes = set(self.boxes)
            updated_boxes.remove(next_position)
            updated_boxes.add(box_destination)

            new_boxes = frozenset(updated_boxes)

        return State(
            player=next_position,
            boxes=new_boxes,
            walls=self.walls,
            goals=self.goals,
            floors=self.floors,
        )

    def get_successors(self):
        """
        Sinh các trạng thái kế tiếp hợp lệ.

        Mỗi phần tử có dạng:
            (action, next_state, step_cost)
        """
        successors = []

        for action in DIRECTIONS:
            next_state = self.move(action)

            if next_state is not None:
                successors.append((action, next_state, 1))

        return successors