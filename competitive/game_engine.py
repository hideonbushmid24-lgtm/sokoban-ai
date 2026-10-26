import random
from dataclasses import dataclass
from enum import Enum

from competitive.competitive_state import CompetitiveState


class Action(str, Enum):
    NORTH = "North"
    EAST = "East"
    WEST = "West"
    SOUTH = "South"
    WAIT = "Wait"


DELTAS = {
    Action.NORTH: (-1, 0),
    Action.EAST: (0, 1),
    Action.WEST: (0, -1),
    Action.SOUTH: (1, 0),
}


@dataclass(frozen=True)
class _Intent:
    """Dự định di chuyển trước khi xử lý xung đột."""

    target: tuple[int, int]
    box_from: tuple[int, int] | None = None
    box_to: tuple[int, int] | None = None


class CompetitiveGameEngine:
    def __init__(self, initial_state, max_steps=20):
        # Kiểm tra max_steps là số nguyên dương.
        initial_state.is_terminal(max_steps)

        self.initial_state = initial_state
        self.state = initial_state
        self.max_steps = max_steps
        self.last_conflict = None

    @classmethod
    def from_map_data(cls, map_data, max_steps=20):
        initial_state = CompetitiveState.from_map_data(map_data)
        return cls(initial_state, max_steps)

    def reset(self):
        self.state = self.initial_state
        self.last_conflict = None

    def is_finished(self):
        return self.state.is_terminal(self.max_steps)

    def get_winner(self):
        return self.state.winner(self.max_steps)

    @classmethod
    def _random_conflict_type(cls, state, first, second):
        """
        Xác định loại tranh chấp phải phân xử bằng xác suất.

        Trả về:
            "same_box": hai agent cùng đẩy một thùng.
            "same_position": hai agent cùng chủ động đi vào một ô.
            None: không có tranh chấp ngẫu nhiên.
        """
        same_box = (
            first.box_from is not None
            and second.box_from is not None
            and first.box_from == second.box_from
        )

        if same_box:
            return "same_box"

        first_moved = first.target != state.agent_1
        second_moved = second.target != state.agent_2

        same_position = (
            first_moved
            and second_moved
            and first.target == second.target
        )

        if same_position:
            return "same_position"

        return None

    @classmethod
    def resolve_turn(
        cls,
        state,
        action_1,
        action_2,
        conflict_p=None,
    ):
        """
        Xử lý một lượt thi đấu thật.

        Nếu có tranh chấp, p được sinh theo phân bố đều liên tục
        trên [0, 1). conflict_p chỉ dùng để tạo kiểm thử xác định.
        """
        action_1 = Action(action_1)
        action_2 = Action(action_2)

        first = cls._make_intent(state, 1, action_1)
        second = cls._make_intent(state, 2, action_2)

        conflict_type = cls._random_conflict_type(
            state,
            first,
            second,
        )

        if conflict_type is None:
            next_state = cls.transition(
                state,
                action_1,
                action_2,
            )
            return next_state, None

        p = (
            random.random()
            if conflict_p is None
            else float(conflict_p)
        )

        if not 0.0 <= p < 1.0:
            raise ValueError(
                "Giá trị xác suất p phải thuộc khoảng [0, 1)."
            )

        winner = 1 if p < 0.5 else 2
        loser = 2 if winner == 1 else 1

        next_state = cls.transition(
            state,
            action_1,
            action_2,
            randomize_conflicts=True,
            conflict_p=p,
        )

        conflict = {
            "type": conflict_type,
            "p": p,
            "winner": winner,
            "loser": loser,
        }

        return next_state, conflict

    @staticmethod
    def _make_intent(state, agent_id, action):
        """
        Tính dự định dựa trên bản đồ ở đầu lượt.

        Chưa xử lý vị trí agent còn lại vì agent đó cũng
        có thể di chuyển trong cùng lượt.
        """
        start = state.position_of(agent_id)
        idle = _Intent(start)

        if action == Action.WAIT:
            return idle

        dr, dc = DELTAS[action]
        target = (start[0] + dr, start[1] + dc)

        if target not in state.floors:
            return idle

        # Đi vào ô không có thùng.
        if target not in state.boxes:
            return _Intent(target)

        # Nếu phía trước có thùng, thử đẩy một ô.
        destination = (target[0] + dr, target[1] + dc)

        if (
            destination not in state.floors
            or destination in state.boxes
        ):
            return idle

        return _Intent(
            target=target,
            box_from=target,
            box_to=destination,
        )

    @classmethod
    def candidate_actions(cls, state, agent_id):
        """
        Các hành động agent có thể đề xuất.

        Xung đột với agent còn lại chỉ được quyết định
        khi biết cả hai hành động.
        """
        start = state.position_of(agent_id)

        return [
            action
            for action in Action
            if action == Action.WAIT
            or cls._make_intent(state, agent_id, action).target != start
        ]

    @classmethod
    def transition(
        cls,
        state,
        action_1,
        action_2,
        *,
        randomize_conflicts=False,
        conflict_p=None,
    ):
        """
        Tính trạng thái sau một lượt, không sửa state đầu vào.

        Hàm này phục vụ cả engine và việc mô phỏng của các agent.
        """
        # Nhận được cả Action.NORTH và chuỗi "North".
        # Chuỗi không hợp lệ sẽ phát sinh ValueError.
        action_1 = Action(action_1)
        action_2 = Action(action_2)

        first = cls._make_intent(state, 1, action_1)
        second = cls._make_intent(state, 2, action_2)

        def cancel_round():
            # Giữ bàn chơi nhưng vẫn tăng số lượt.
            return state.next_state(
                agent_1=state.agent_1,
                agent_2=state.agent_2,
                boxes=state.boxes,
                box_owners=dict(state.box_owners),
            )

        conflict_type = cls._random_conflict_type(
            state,
            first,
            second,
        )

        if conflict_type is not None:
            # Các agent dùng transition() để mô phỏng khi tìm kiếm.
            # Khi mô phỏng, giữ cách xử lý xác định: hủy xung đột.
            if not randomize_conflicts:
                return cancel_round()

            p = (
                random.random()
                if conflict_p is None
                else float(conflict_p)
            )

            if not 0.0 <= p < 1.0:
                raise ValueError(
                    "Giá trị xác suất p phải thuộc khoảng [0, 1)."
                )

            if p < 0.5:
                # Agent 1 thắng; Agent 2 đứng yên và mất lượt.
                second = _Intent(state.agent_2)
            else:
                # Agent 2 thắng; Agent 1 đứng yên và mất lượt.
                first = _Intent(state.agent_1)

        # Trường hợp một agent đi vào agent đang đứng yên.
        if first.target == second.target:
            return cancel_round()

        # Hai agent đổi chỗ trực tiếp vẫn bị chặn.
        if (
            first.target == state.agent_2
            and second.target == state.agent_1
        ):
            return cancel_round()

        owners = dict(state.box_owners)
        intents = ((1, first), (2, second))

        # Xóa vị trí cũ của các thùng được đẩy.
        for _, intent in intents:
            if intent.box_from is not None:
                del owners[intent.box_from]

        # Thêm vị trí mới và cập nhật quyền sở hữu.
        for agent_id, intent in intents:
            if intent.box_from is not None:
                # Hai thùng không được tới cùng một ô.
                if intent.box_to in owners:
                    return cancel_round()

                owners[intent.box_to] = (
                    agent_id
                    if intent.box_to in state.goals
                    else 0
                )

        # Không để agent và thùng trùng vị trí sau lượt.
        if first.target in owners or second.target in owners:
            return cancel_round()

        return state.next_state(
            agent_1=first.target,
            agent_2=second.target,
            boxes=set(owners),
            box_owners=owners,
        )

    def step(self, action_1, action_2):
        """Thực hiện một lượt thật trong trận đấu."""
        if self.is_finished():
            raise RuntimeError("Trận đấu đã kết thúc.")

        self.state, self.last_conflict = self.resolve_turn(
            self.state,
            action_1,
            action_2,
        )

        return self.state