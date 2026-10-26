from competitive.competitive_state import CompetitiveState
from competitive.game_engine import Action
from competitive.match_runner import MatchRunner


def make_state():
    """Tạo bản đồ kiểm thử với hai thùng ngay dưới hai đích."""
    floors = frozenset(
        (r, c)
        for r in range(1, 6)
        for c in range(1, 8)
    )

    walls = frozenset(
        (r, c)
        for r in range(7)
        for c in range(9)
        if (r, c) not in floors
    )

    boxes = frozenset({
        (2, 3),
        (2, 5),
    })

    return CompetitiveState(
        agent_1=(3, 3),
        agent_2=(3, 5),
        boxes=boxes,
        walls=walls,
        goals=frozenset({
            (1, 3),
            (1, 5),
        }),
        floors=floors,
        box_owners=frozenset(
            (box, 0) for box in boxes
        ),
        step_count=0,
    )


class ScriptedAgent:
    """Agent trả hành động theo kịch bản có sẵn."""

    def __init__(self, agent_id, actions):
        self.agent_id = agent_id
        self.actions = actions
        self.last_stats = {}

    def choose_action(self, state, remaining_steps=None):
        if state.step_count == 0:
            assert state.scores == (0, 0), (
                "Nhận sai trạng thái đầu lượt!"
            )

        self.last_stats = {
            "remaining_steps": remaining_steps
        }

        if state.step_count < len(self.actions):
            return self.actions[state.step_count]

        return Action.WAIT


class ErrorAgent(ScriptedAgent):
    def choose_action(self, state, remaining_steps=None):
        raise ValueError("Lỗi giả lập")


class InvalidAgent(ScriptedAgent):
    def choose_action(self, state, remaining_steps=None):
        return "Fly"


class SlowAgent(ScriptedAgent):
    def choose_action(self, state, remaining_steps=None):
        from time import sleep

        sleep(5)
        return Action.NORTH


def main():
    initial = make_state()

    # 1. Cả hai agent đẩy North và cùng ghi điểm.
    result = MatchRunner(
        initial,
        ScriptedAgent(1, [Action.NORTH]),
        ScriptedAgent(2, [Action.NORTH]),
        max_steps=3,
    ).run()

    assert result["scores"] == (1, 1)
    assert result["winner"] == 0

    assert all(
        turn[key]["status"] == "ok"
        for turn in result["history"]
        for key in ("agent_1", "agent_2")
    )

    print(
        "1. Hai agent nhận cùng trạng thái "
        "và cùng ghi điểm: PASS"
    )

    # 2. Trận đấu phải chạy đủ lượt dù các thùng đã ở đích.
    assert result["steps_played"] == 3
    assert len(result["history"]) == 3
    assert len(result["states"]) == 4
    assert result["final_state"].step_count == 3

    for index, turn in enumerate(result["history"]):
        assert (
            turn["state_before"]
            == result["states"][index]
        )

        assert (
            turn["state_after"]
            == result["states"][index + 1]
        )

        for key in ("agent_1", "agent_2"):
            assert (
                turn[key]["stats"]["remaining_steps"]
                == 3 - index
            )

    assert initial == make_state()

    print(
        "2. Đủ số lượt, đúng lịch sử "
        "và giữ nguyên trạng thái đầu: PASS"
    )

    # 3. Kiểm tra cả trường hợp Agent1 thắng và Agent2 thắng.
    for winner in (1, 2):
        result = MatchRunner(
            initial,
            ScriptedAgent(
                1,
                [Action.NORTH] if winner == 1 else [],
            ),
            ScriptedAgent(
                2,
                [Action.NORTH] if winner == 2 else [],
            ),
            max_steps=1,
        ).run()

        assert result["winner"] == winner

    print("3. Xác định đúng agent thắng: PASS")

    # 4. Agent gặp lỗi hoặc trả hành động không hợp lệ.
    for agent_class in (ErrorAgent, InvalidAgent):
        result = MatchRunner(
            initial,
            agent_class(1, []),
            ScriptedAgent(2, [Action.NORTH]),
            max_steps=1,
        ).run()

        decision = result["history"][0]["agent_1"]

        assert decision["status"] == "error"
        assert decision["action"] == Action.WAIT
        assert result["scores"] == (0, 1)

    print(
        "4. Agent lỗi hoặc trả hành động sai "
        "được thay bằng Wait: PASS"
    )

    # 5. Agent ngủ 5 giây, nhưng chỉ được chờ 200 ms mỗi lượt.
    # Tiến trình quá giờ phải bị dừng và trận đấu vẫn tiếp tục.
    result = MatchRunner(
        initial,
        SlowAgent(1, []),
        ScriptedAgent(2, [Action.NORTH]),
        max_steps=2,
        time_limit_ms=200,
    ).run()

    for turn in result["history"]:
        assert turn["agent_1"]["status"] == "timeout"
        assert turn["agent_1"]["action"] == Action.WAIT
        assert turn["agent_2"]["status"] == "ok"

    assert result["scores"] == (0, 1)

    print(
        "5. Ngắt agent quá giờ "
        "và tiếp tục trận đấu: PASS"
    )

    print("Tất cả kiểm thử MatchRunner đã thành công.")


if __name__ == "__main__":
    main()