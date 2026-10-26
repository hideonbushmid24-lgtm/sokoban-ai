from collections import deque
from heapq import heappop, heappush
from itertools import count
from math import inf
from time import perf_counter

from competitive.game_engine import Action, CompetitiveGameEngine


class Agent2:
    """Agent tìm kiếm bằng Greedy Best-First Search."""

    def __init__(
        self,
        agent_id=2,
        time_limit_ms=900,
        max_depth=30,
        max_nodes=5000,
    ):
        if agent_id not in (1, 2):
            raise ValueError("Agent ID phải là 1 hoặc 2.")

        if not 0 < time_limit_ms <= 1000:
            raise ValueError(
                "Ngân sách thời gian phải lớn hơn 0 "
                "và tối đa 1000 ms."
            )

        if not isinstance(max_depth, int) or max_depth < 1:
            raise ValueError("max_depth phải là số nguyên dương.")

        if not isinstance(max_nodes, int) or max_nodes < 1:
            raise ValueError("max_nodes phải là số nguyên dương.")

        self.agent_id = agent_id
        self.time_limit_ms = time_limit_ms
        self.max_depth = max_depth
        self.max_nodes = max_nodes

        self.last_stats = {}

        self._map_key = None
        self._distance_cache = {}

    @staticmethod
    def _state_key(state):
        # Bỏ step_count để nhận diện các cấu hình bàn cờ trùng nhau.
        # Quyền sở hữu thùng vẫn phải nằm trong khóa.
        return (
            state.agent_1,
            state.agent_2,
            state.boxes,
            state.box_owners,
        )

    def _utility(self, state):
        scores = state.scores

        own_score = scores[self.agent_id - 1]
        other_score = scores[2 - self.agent_id]

        # Ưu tiên chênh lệch điểm, sau đó đến điểm của chính mình.
        return own_score - other_score, own_score

    def _prepare_map(self, state):
        map_key = (state.floors, state.goals)

        if map_key != self._map_key:
            self._map_key = map_key
            self._distance_cache = {}

    @staticmethod
    def _check_deadline(deadline):
        if deadline is not None and perf_counter() >= deadline:
            raise TimeoutError

    def _distances_from(self, start, floors, deadline=None):
        """
        Khoảng cách BFS trên bản đồ tĩnh.

        Có xét tường, nhưng bỏ qua thùng và agent còn lại.
        Chỉ lưu cache khi BFS đã hoàn thành.
        """
        self._check_deadline(deadline)

        if start in self._distance_cache:
            return self._distance_cache[start]

        distances = {start: 0}
        queue = deque([start])

        directions = (
            (-1, 0),
            (0, 1),
            (0, -1),
            (1, 0),
        )

        while queue:
            self._check_deadline(deadline)

            row, col = queue.popleft()

            for dr, dc in directions:
                neighbor = (row + dr, col + dc)

                if neighbor not in floors:
                    continue

                if neighbor in distances:
                    continue

                distances[neighbor] = distances[(row, col)] + 1
                queue.append(neighbor)

        self._distance_cache[start] = distances
        return distances

    def _estimate(self, state, deadline=None):
        """
        Ước lượng khoảng cách tới một cơ hội cải thiện điểm.

        - Thùng trung lập: tiếp cận thùng + đưa thùng tới đích.
        - Thùng của đối thủ: tiếp cận để có thể đẩy thùng.
        - Thùng của mình: không chọn làm mục tiêu.

        Đây là heuristic định hướng, không phải đường đẩy hợp lệ.
        """
        self._check_deadline(deadline)

        player = state.position_of(self.agent_id)

        player_distances = self._distances_from(
            player,
            state.floors,
            deadline,
        )

        estimates = []

        for box in state.boxes:
            self._check_deadline(deadline)

            owner = state.owner_of(box)

            if owner == self.agent_id:
                continue

            approach = player_distances.get(box, inf)

            if approach == inf:
                continue

            # Ước lượng khoảng cách tới ô cạnh thùng.
            approach = max(0, approach - 1)

            if owner in (1, 2) and owner != self.agent_id:
                estimates.append(approach)
                continue

            box_distances = self._distances_from(
                box,
                state.floors,
                deadline,
            )

            goal_distance = inf

            for goal in state.goals:
                self._check_deadline(deadline)

                goal_distance = min(
                    goal_distance,
                    box_distances.get(goal, inf),
                )

            if goal_distance != inf:
                estimates.append(approach + goal_distance)

        return min(estimates, default=inf)

    def _simulate(self, state, action):
        # Khi lập kế hoạch, giả định đối thủ đứng yên.
        if self.agent_id == 1:
            return CompetitiveGameEngine.transition(
                state,
                action,
                Action.WAIT,
            )

        return CompetitiveGameEngine.transition(
            state,
            Action.WAIT,
            action,
        )

    def choose_action(self, state, remaining_steps=None):
        if remaining_steps is not None:
            if (
                not isinstance(remaining_steps, int)
                or remaining_steps < 0
            ):
                raise ValueError(
                    "Số lượt còn lại phải là số nguyên không âm."
                )

        start = perf_counter()
        deadline = start + self.time_limit_ms / 1000

        expanded = 0
        generated = 1

        def finish(action, reason):
            self.last_stats = {
                "action": action.value,
                "nodes_expanded": expanded,
                "nodes_generated": generated,
                "time_ms": (perf_counter() - start) * 1000,
                "reason": reason,
            }
            return action

        if remaining_steps == 0:
            return finish(Action.WAIT, "no_turns")

        depth_limit = self.max_depth

        if remaining_steps is not None:
            depth_limit = min(depth_limit, remaining_steps)

        self._prepare_map(state)
        baseline = self._utility(state)

        try:
            root_h = self._estimate(state, deadline)
        except TimeoutError:
            return finish(Action.WAIT, "time_limit")

        if root_h == inf:
            return finish(Action.WAIT, "no_opportunity")

        order = count()

        # Phần tử heap:
        # (heuristic, thứ tự, trạng thái, hành động đầu tiên, độ sâu)
        frontier = [
            (root_h, next(order), state, None, 0)
        ]

        # Cho phép xét lại trạng thái nếu tìm được đường ngắn hơn.
        best_depth = {
            self._state_key(state): 0
        }

        reached_depth_limit = False

        while frontier:
            if perf_counter() >= deadline:
                return finish(Action.WAIT, "time_limit")

            _, _, current, first_action, depth = heappop(frontier)

            current_key = self._state_key(current)

            # Bỏ bản ghi cũ nếu đã có đường ngắn hơn tới trạng thái này.
            if depth != best_depth.get(current_key):
                continue

            if depth >= depth_limit:
                reached_depth_limit = True
                continue

            if expanded >= self.max_nodes:
                return finish(Action.WAIT, "node_limit")

            expanded += 1

            actions = CompetitiveGameEngine.candidate_actions(
                current,
                self.agent_id,
            )

            for action in actions:
                if perf_counter() >= deadline:
                    return finish(Action.WAIT, "time_limit")

                if action == Action.WAIT:
                    continue

                next_state = self._simulate(current, action)
                generated += 1

                key = self._state_key(next_state)
                next_depth = depth + 1

                if next_depth >= best_depth.get(key, inf):
                    continue

                chosen_first = (
                    action
                    if first_action is None
                    else first_action
                )

                if perf_counter() >= deadline:
                    return finish(Action.WAIT, "time_limit")

                # Kiểm tra cải thiện điểm TRƯỚC khi tính heuristic.
                # Trạng thái ghi điểm không bị bỏ lỡ khi h = vô cùng.
                if self._utility(next_state) > baseline:
                    return finish(
                        chosen_first,
                        "improved_score",
                    )

                try:
                    priority = self._estimate(
                        next_state,
                        deadline,
                    )
                except TimeoutError:
                    return finish(Action.WAIT, "time_limit")

                if priority == inf:
                    continue

                best_depth[key] = next_depth

                heappush(
                    frontier,
                    (
                        priority,
                        next(order),
                        next_state,
                        chosen_first,
                        next_depth,
                    ),
                )

        reason = (
            "depth_limit"
            if reached_depth_limit
            else "no_improvement"
        )

        return finish(Action.WAIT, reason)