from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from competitive.agent_1 import Agent1
from competitive.competitive_map_loader import CompetitiveMapLoader
from competitive.competitive_state import CompetitiveState
from competitive.game_engine import (
    Action,
    CompetitiveGameEngine,
)


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def make_state(layout):
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "test_map.txt"
        path.write_text(layout, encoding="utf-8")

        return CompetitiveState.from_map_data(
            CompetitiveMapLoader(path)
        )


def main():
    map_data = CompetitiveMapLoader(
        MAPS_DIR / "map_competitive_test.txt"
    )
    initial = CompetitiveState.from_map_data(map_data)

    agent = Agent1(agent_id=1)

    # 1. Agent 1 có thể ghi điểm ngay bằng North.
    action = agent.choose_action(initial, remaining_steps=20)

    assert action == Action.NORTH

    next_state = CompetitiveGameEngine.transition(
        initial,
        action,
        Action.WAIT,
    )

    assert next_state.scores == (1, 0)

    print("1. Chọn North để ghi điểm: PASS")
    print("Hành động:", action.value)
    print(f"Thời gian quyết định: {agent.last_stats['time_ms']:.3f} ms")

    # 2. Bàn chơi cần East, East, North mới ghi điểm.
    multi_step_initial = make_state(
        "%%%%%%%%\n"
        "%  D   %\n"
        "%  B   %\n"
        "%1   2 %\n"
        "%      %\n"
        "%%%%%%%%\n"
    )

    state = multi_step_initial
    actions = []

    for index in range(3):
        action = agent.choose_action(
            state,
            remaining_steps=3 - index,
        )

        actions.append(action.value)

        state = CompetitiveGameEngine.transition(
            state,
            action,
            Action.WAIT,
        )

    assert actions == ["East", "East", "North"]
    assert state.scores == (1, 0)

    print("2. Tìm kế hoạch nhiều bước: PASS")
    print("Chuỗi hành động:", actions)

    # 3. Không tìm thấy cách cải thiện điểm trên map bị kẹt.
    blocked = make_state(
        "%%%%%%%\n"
        "%1   2%\n"
        "%B   D%\n"
        "%%%%%%%\n"
    )

    assert agent.choose_action(blocked) == Action.WAIT
    assert agent.last_stats["reason"] == "no_improvement"

    print("3. Không cải thiện được điểm thì chọn Wait: PASS")

    # 4. Không lập kế hoạch dài hơn số lượt còn lại.
    assert agent.choose_action(
        multi_step_initial,
        remaining_steps=1,
    ) == Action.WAIT

    assert agent.choose_action(
        initial,
        remaining_steps=0,
    ) == Action.WAIT

    print("4. Tôn trọng số lượt còn lại: PASS")

    # 5. Giới hạn node.
    limited_agent = Agent1(max_nodes=1)

    assert limited_agent.choose_action(
        multi_step_initial
    ) == Action.WAIT

    assert limited_agent.last_stats["reason"] == "node_limit"

    print("5. Giới hạn số node mở rộng: PASS")

    # 6. Giả lập đồng hồ để kiểm tra nhánh hết thời gian.
    # Không phải phép đo tốc độ thật.
    with patch(
        "competitive.agent_1.perf_counter",
        side_effect=[0.0, 2.0, 2.0],
    ):
        assert agent.choose_action(initial) == Action.WAIT
        assert agent.last_stats["reason"] == "time_limit"

    print("6. Xử lý hết ngân sách thời gian: PASS")

    # 7. Không thay đổi trạng thái đầu vào.
    assert initial.step_count == 0
    assert initial.scores == (0, 0)

    # Cùng bàn chơi ở lượt khác có cùng khóa tìm kiếm.
    later = replace(initial, step_count=99)

    assert agent._state_key(initial) == agent._state_key(later)

    print("7. Giữ nguyên trạng thái và nhận diện vòng lặp: PASS")

    # 8. Agent có thể tìm cách giảm điểm đối thủ.
    state = CompetitiveGameEngine.transition(
        initial,
        Action.NORTH,
        Action.NORTH,
    )

    assert state.scores == (1, 1)

    for _ in range(3):
        action = agent.choose_action(state)

        state = CompetitiveGameEngine.transition(
            state,
            action,
            Action.WAIT,
        )

    assert state.scores == (1, 0)

    print("8. Tìm cách đẩy thùng đối thủ khỏi đích: PASS")

    print("\nTất cả kiểm thử Agent1 đã thành công.")


if __name__ == "__main__":
    main()