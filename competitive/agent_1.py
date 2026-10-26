from collections import deque
from time import perf_counter

from competitive.game_engine import Action, CompetitiveGameEngine


class Agent1:
    """Agent chọn hành động bằng BFS có giới hạn tìm kiếm."""

    def __init__(
        self,
        agent_id=1,
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

    @staticmethod
    def _state_key(state):
        """
        Nhận diện cấu hình bàn chơi.

        Không đưa step_count vào khóa để tránh xem việc quay lại
        cùng bàn chơi ở lượt khác là một trạng thái mới.
        """
        return (
            state.agent_1,
            state.agent_2,
            state.boxes,
            state.box_owners,
        )

    def _utility(self, state):
        scores = state.scores

        own = scores[self.agent_id - 1]
        other = scores[2 - self.agent_id]

        return own - other, own

    def _simulate(self, state, action):
        """Khi lập kế hoạch, tạm giả định đối thủ đứng yên."""
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
        """
        Chọn một hành động từ bàn chơi hiện tại.

        remaining_steps: số lượt còn lại của trận đấu.
        """
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

        baseline = self._utility(state)

        # Mỗi phần tử: trạng thái, hành động đầu tiên, độ sâu.
        queue = deque([(state, None, 0)])
        visited = {self._state_key(state)}

        reached_depth_limit = False

        while queue:
            if perf_counter() >= deadline:
                return finish(Action.WAIT, "time_limit")

            if expanded >= self.max_nodes:
                return finish(Action.WAIT, "node_limit")

            current, first_action, depth = queue.popleft()

            if depth >= depth_limit:
                reached_depth_limit = True
                continue

            expanded += 1

            actions = CompetitiveGameEngine.candidate_actions(
                current,
                self.agent_id,
            )

            for action in actions:
                if perf_counter() >= deadline:
                    return finish(Action.WAIT, "time_limit")

                # Trong mô hình đối thủ đứng yên, Wait không
                # tạo ra cấu hình bàn chơi mới để tìm kiếm.
                if action == Action.WAIT:
                    continue

                next_state = self._simulate(current, action)
                generated += 1

                key = self._state_key(next_state)

                if key in visited:
                    continue

                visited.add(key)

                chosen_first = (
                    action
                    if first_action is None
                    else first_action
                )

                # BFS tìm được một chuỗi giúp cải thiện điểm.
                if self._utility(next_state) > baseline:
                    return finish(
                        chosen_first,
                        "improved_score",
                    )

                queue.append(
                    (
                        next_state,
                        chosen_first,
                        depth + 1,
                    )
                )

        reason = (
            "depth_limit"
            if reached_depth_limit
            else "no_improvement"
        )

        return finish(Action.WAIT, reason)