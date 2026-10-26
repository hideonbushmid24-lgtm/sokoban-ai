from collections import deque
from functools import lru_cache
from math import inf

from core.state import DIRECTIONS


class Heuristic:
    """Khoảng cách BFS kết hợp ghép thùng với đích."""

    def __init__(self, initial_state):
        self.floors = initial_state.floors
        self.goals = tuple(sorted(initial_state.goals))

        # Với mỗi đích, BFS một lần đến các ô nền.
        self.distances = [
            self._bfs(goal)
            for goal in self.goals
        ]

        # Cùng vị trí thùng thì có cùng giá trị heuristic.
        self.cache = {}

    def _bfs(self, start):
        """Tính khoảng cách từ start đến các ô nền có thể tới."""
        distances = {start: 0}
        queue = deque([start])

        while queue:
            row, col = queue.popleft()

            for dr, dc in DIRECTIONS.values():
                neighbor = (row + dr, col + dc)

                if (
                    neighbor in self.floors
                    and neighbor not in distances
                ):
                    distances[neighbor] = distances[(row, col)] + 1
                    queue.append(neighbor)

        return distances

    def estimate(self, state):
        """Trả về h(state): chi phí còn lại được ước lượng."""
        if (
            state.floors != self.floors
            or state.goals != frozenset(self.goals)
        ):
            raise ValueError("Trạng thái thuộc bản đồ khác.")

        boxes = tuple(sorted(state.boxes))

        if boxes in self.cache:
            return self.cache[boxes]

        if len(boxes) > len(self.goals):
            return inf

        @lru_cache(maxsize=None)
        def match(box_index, used_goals):
            """
            Ghép các thùng từ box_index trở đi.

            used_goals là số nguyên dùng các bit để đánh dấu
            những đích đã được chọn.
            """
            if box_index == len(boxes):
                return 0

            best = inf
            box = boxes[box_index]

            for goal_index, distances in enumerate(self.distances):
                goal_bit = 1 << goal_index

                # Bỏ qua đích đã ghép với thùng trước đó.
                if used_goals & goal_bit:
                    continue

                distance = distances.get(box, inf)

                # Không có đường nối ô thùng với ô đích.
                if distance == inf:
                    continue

                remaining = match(
                    box_index + 1,
                    used_goals | goal_bit,
                )

                best = min(best, distance + remaining)

            return best

        result = match(0, 0)
        self.cache[boxes] = result

        return result