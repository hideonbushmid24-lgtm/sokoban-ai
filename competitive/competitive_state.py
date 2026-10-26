from dataclasses import dataclass


Position = tuple[int, int]


@dataclass(frozen=True)
class CompetitiveState:
    """Trạng thái bất biến của trận đấu hai agent."""

    agent_1: Position
    agent_2: Position

    boxes: frozenset[Position]
    walls: frozenset[Position]
    goals: frozenset[Position]
    floors: frozenset[Position]

    # Mỗi phần tử là ((hàng, cột), chủ_sở_hữu).
    box_owners: frozenset[tuple[Position, int]]

    step_count: int = 0

    def __post_init__(self):
        """Chuẩn hóa tập hợp và kiểm tra dữ liệu trạng thái."""
        for name in (
            "boxes", "walls", "goals", "floors", "box_owners"
        ):
            object.__setattr__(
                self,
                name,
                frozenset(getattr(self, name)),
            )

        if not isinstance(self.step_count, int) or self.step_count < 0:
            raise ValueError("Số lượt phải là số nguyên không âm.")

        if self.walls & self.floors:
            raise ValueError("Tường và ô nền không được trùng nhau.")

        if (
            not self.boxes <= self.floors
            or not self.goals <= self.floors
        ):
            raise ValueError("Thùng và đích phải nằm trên ô nền.")

        if (
            self.agent_1 not in self.floors
            or self.agent_2 not in self.floors
        ):
            raise ValueError("Agent phải nằm trên ô nền.")

        if self.agent_1 == self.agent_2:
            raise ValueError("Hai agent không được đứng cùng một ô.")

        if self.agent_1 in self.boxes or self.agent_2 in self.boxes:
            raise ValueError("Agent không được đứng trùng với thùng.")

        owners = dict(self.box_owners)

        if len(owners) != len(self.box_owners):
            raise ValueError(
                "Một thùng không được có nhiều chủ sở hữu."
            )

        if set(owners) != set(self.boxes):
            raise ValueError(
                "Mỗi thùng phải có đúng một thông tin sở hữu."
            )

        for position, owner in owners.items():
            if owner not in (0, 1, 2):
                raise ValueError(
                    "Chủ sở hữu chỉ được là 0, 1 hoặc 2."
                )

            if owner != 0 and position not in self.goals:
                raise ValueError(
                    "Thùng ngoài đích phải có chủ sở hữu là 0."
                )

    @classmethod
    def from_map_data(cls, map_data):
        """Tạo trạng thái ban đầu từ CompetitiveMapLoader."""
        return cls(
            agent_1=map_data.agent_1,
            agent_2=map_data.agent_2,
            boxes=frozenset(map_data.boxes),
            walls=frozenset(map_data.walls),
            goals=frozenset(map_data.goals),
            floors=frozenset(map_data.floors),
            box_owners=frozenset(map_data.box_owners.items()),
            step_count=0,
        )

    def position_of(self, agent_id):
        if agent_id == 1:
            return self.agent_1

        if agent_id == 2:
            return self.agent_2

        raise ValueError("Agent ID phải là 1 hoặc 2.")

    def owner_of(self, position):
        """
        Trả về 0, 1 hoặc 2 nếu ô có thùng.
        Trả về None nếu ô không có thùng.
        """
        return dict(self.box_owners).get(position)

    @property
    def neutral_boxes(self):
        """Các thùng chưa thuộc agent nào."""
        return frozenset(
            position
            for position, owner in self.box_owners
            if owner == 0
        )

    @property
    def scores(self):
        """Điểm hiện tại theo thứ tự (agent 1, agent 2)."""
        score_1 = sum(
            owner == 1
            for _, owner in self.box_owners
        )

        score_2 = sum(
            owner == 2
            for _, owner in self.box_owners
        )

        return score_1, score_2

    def all_boxes_on_goals(self):
        """Thông tin bàn chơi, không phải điều kiện kết thúc."""
        return self.boxes.issubset(self.goals)

    def is_terminal(self, max_steps):
        if not isinstance(max_steps, int) or max_steps < 1:
            raise ValueError(
                "Giới hạn lượt phải là số nguyên dương."
            )

        return self.step_count >= max_steps

    def winner(self, max_steps):
        """
        None: trận đấu chưa kết thúc.
        0: hòa.
        1 hoặc 2: agent thắng.
        """
        if not self.is_terminal(max_steps):
            return None

        score_1, score_2 = self.scores

        if score_1 > score_2:
            return 1

        if score_2 > score_1:
            return 2

        return 0

    def next_state(
        self,
        *,
        agent_1,
        agent_2,
        boxes,
        box_owners,
    ):
        """
        Tạo trạng thái sau một lượt.

        Engine sẽ tính vị trí và quyền sở hữu trước khi gọi hàm.
        box_owners truyền vào là dict: {vị_trí_thùng: chủ_sở_hữu}.
        """
        return CompetitiveState(
            agent_1=agent_1,
            agent_2=agent_2,
            boxes=frozenset(boxes),
            walls=self.walls,
            goals=self.goals,
            floors=self.floors,
            box_owners=frozenset(box_owners.items()),
            step_count=self.step_count + 1,
        )