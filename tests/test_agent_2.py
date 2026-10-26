from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from competitive.agent_2 import Agent2
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
    agent = Agent2(agent_id=2)

    # 1. Agent 2 có thể ghi điểm ngay bằng North.
    action = agent.choose_action(
        initial,
        remaining_steps=20,
    )

    assert action == Action.NORTH

    next_state = CompetitiveGameEngine.transition(
        initial,
        Action.WAIT,
        action,
    )

    assert next_state.scores == (0, 1)

    print("1. Chọn North để ghi điểm: PASS")
    print("Hành động:", action.value)
    print(
        "Thuật toán: GBFS | "
        f"Thời gian: {agent.last_stats['time_ms']:.3f} ms"
    )

    # 2. Kiểm tra kế hoạch nhiều bước:
    # Agent 2 cần West, West, North.
    multi_step = make_state(
        "%%%%%%%%\n"
        "%   D  %\n"
        "%   B  %\n"
        "% 1   2%\n"
        "%      %\n"
        "%%%%%%%%\n"
    )

    state = multi_step
    actions = []

    for index in range(3):
        action = agent.choose_action(
            state,
            remaining_steps=3 - index,
        )

        actions.append(action.value)

        state = CompetitiveGameEngine.transition(
            state,
            Action.WAIT,
            action,
        )

    assert actions == ["West", "West", "North"]
    assert state.scores == (0, 1)

    print("2. GBFS tìm kế hoạch nhiều bước: PASS")
    print("Chuỗi hành động:", actions)

    # 3. Bản đồ có thùng bị kẹt.
    blocked = make_state(
        "%%%%%%%\n"
        "%1   2%\n"
        "%B   D%\n"
        "%%%%%%%\n"
    )

    action = agent.choose_action(blocked)

    assert action == Action.WAIT
    assert agent.last_stats["reason"] in {
        "no_opportunity",
        "no_improvement",
    }

    print("3. Không có cơ hội ghi điểm thì chọn Wait: PASS")

    # 4. Số lượt còn lại không đủ hoàn thành kế hoạch.
    action = agent.choose_action(
        multi_step,
        remaining_steps=1,
    )

    assert action == Action.WAIT
    assert agent.last_stats["reason"] == "depth_limit"

    assert agent.choose_action(
        initial,
        remaining_steps=0,
    ) == Action.WAIT

    print("4. Tôn trọng số lượt còn lại: PASS")

    # 5. Kiểm tra giới hạn node.
    limited_agent = Agent2(max_nodes=1)

    assert limited_agent.choose_action(
        multi_step
    ) == Action.WAIT

    assert limited_agent.last_stats["reason"] == "node_limit"

    print("5. Giới hạn số node mở rộng: PASS")

    # 6. Giả lập hết thời gian.
    with patch(
        "competitive.agent_2.perf_counter",
        side_effect=[0.0, 2.0, 2.0],
    ):
        assert agent.choose_action(initial) == Action.WAIT
        assert agent.last_stats["reason"] == "time_limit"

    print("6. Xử lý hết ngân sách thời gian: PASS")

    # 7. Agent không thay đổi state đầu vào.
    assert initial.step_count == 0
    assert initial.scores == (0, 0)

    later = replace(initial, step_count=99)

    assert agent._state_key(initial) == agent._state_key(later)

    print("7. Giữ nguyên trạng thái và tránh vòng lặp: PASS")

    # 8. Agent 2 tìm cách phá điểm của Agent 1.
    state = CompetitiveGameEngine.transition(
        initial,
        Action.NORTH,
        Action.NORTH,
    )

    assert state.scores == (1, 1)

    actions = []

    for _ in range(3):
        action = agent.choose_action(state)
        actions.append(action.value)

        state = CompetitiveGameEngine.transition(
            state,
            Action.WAIT,
            action,
        )

    assert actions == ["West", "North", "West"]
    assert state.scores == (0, 1)

    print("8. Tìm cách đẩy thùng đối thủ khỏi đích: PASS")
    print("Chuỗi hành động:", actions)

    # 9. Có thể cấu hình Agent2 điều khiển phía Agent 1.
    agent_left = Agent2(agent_id=1)

    assert agent_left.choose_action(initial) == Action.NORTH

    print("9. Hỗ trợ cả hai agent ID: PASS")

    print("\nTất cả kiểm thử Agent2 đã thành công.")


if __name__ == "__main__":
    main()