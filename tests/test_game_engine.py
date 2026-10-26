from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from competitive.competitive_map_loader import CompetitiveMapLoader
from competitive.game_engine import (
    Action as A,
    CompetitiveGameEngine,
)


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def make_engine(layout, max_steps=20):
    """Tạo engine từ bản đồ tạm dành riêng cho kiểm thử."""
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "test_map.txt"
        path.write_text(layout, encoding="utf-8")

        map_data = CompetitiveMapLoader(path)

        return CompetitiveGameEngine.from_map_data(
            map_data,
            max_steps=max_steps,
        )


def assert_cancelled(engine, action_1, action_2):
    """Kiểm tra bàn chơi giữ nguyên nhưng lượt vẫn tăng."""
    before = engine.state
    after = engine.step(action_1, action_2)

    assert after.agent_1 == before.agent_1
    assert after.agent_2 == before.agent_2
    assert after.boxes == before.boxes
    assert after.box_owners == before.box_owners
    assert after.step_count == before.step_count + 1


def main():
    # 1. Hai agent cùng đẩy thùng lên đích.
    map_data = CompetitiveMapLoader(
        MAPS_DIR / "map_competitive_test.txt"
    )

    engine = CompetitiveGameEngine.from_map_data(
        map_data,
        max_steps=1,
    )

    state = engine.step(A.NORTH, A.NORTH)

    assert state.agent_1 == (2, 3)
    assert state.agent_2 == (2, 5)
    assert state.scores == (1, 1)
    assert state.step_count == 1
    assert engine.is_finished()
    assert engine.get_winner() == 0

    print("Hai agent ghi điểm đồng thời: PASS")

    # 2. Không chạy thêm lượt sau khi hết trận.
    try:
        engine.step(A.WAIT, A.WAIT)
    except RuntimeError:
        print("Chặn lượt sau khi kết thúc: PASS")
    else:
        raise AssertionError("Engine chưa chặn trận đã kết thúc.")

    engine.reset()

    assert engine.state.step_count == 0
    assert engine.state.scores == (0, 0)
    assert not engine.is_finished()

    print("Đặt lại trận đấu: PASS")

    # 3. Agent 1 bị tường chặn, agent 2 vẫn đi được.
    engine = make_engine(
        "%%%%%%%\n"
        "%1% 2 %\n"
        "% B D %\n"
        "%%%%%%%\n"
    )

    state = engine.step(A.EAST, A.EAST)

    assert state.agent_1 == (1, 1)
    assert state.agent_2 == (1, 5)

    print("Hành động bị chặn được xử lý độc lập: PASS")
    # 4. Hai agent cùng đi vào một vị trí.
    same_position_layout = (
        "%%%%%%%\n"
        "% 1 2 %\n"
        "% B D %\n"
        "%%%%%%%\n"
    )

    # p < 0.5: Agent 1 thắng, Agent 2 đứng yên.
    engine = make_engine(same_position_layout)

    with patch(
        "competitive.game_engine.random.random",
        return_value=0.49,
    ):
        state = engine.step(A.EAST, A.WEST)

    assert state.agent_1 == (1, 3)
    assert state.agent_2 == (1, 4)
    assert state.step_count == 1

    assert engine.last_conflict is not None
    assert engine.last_conflict["type"] == "same_position"
    assert engine.last_conflict["p"] == 0.49
    assert engine.last_conflict["winner"] == 1
    assert engine.last_conflict["loser"] == 2

    print("Cùng vào một ô, p < 0.5, Agent 1 thắng: PASS")

    # p >= 0.5: Agent 2 thắng, Agent 1 đứng yên.
    engine = make_engine(same_position_layout)

    with patch(
        "competitive.game_engine.random.random",
        return_value=0.50,
    ):
        state = engine.step(A.EAST, A.WEST)

    assert state.agent_1 == (1, 2)
    assert state.agent_2 == (1, 3)
    assert state.step_count == 1

    assert engine.last_conflict is not None
    assert engine.last_conflict["type"] == "same_position"
    assert engine.last_conflict["p"] == 0.50
    assert engine.last_conflict["winner"] == 2
    assert engine.last_conflict["loser"] == 1

    print("Cùng vào một ô, p >= 0.5, Agent 2 thắng: PASS")

    # 5. Hai agent cùng đẩy một thùng.
    #
    # Hai agent đứng vuông góc với thùng để hành động của agent
    # thắng có thể thực hiện trong khi agent thua đứng yên.
    same_box_layout = (
        "%%%%%%%\n"
        "%  2  %\n"
        "% 1B D%\n"
        "%     %\n"
        "%%%%%%%\n"
    )

    # p < 0.5: Agent 1 đẩy thùng sang phải.
    engine = make_engine(same_box_layout)

    with patch(
        "competitive.game_engine.random.random",
        return_value=0.49,
    ):
        state = engine.step(A.EAST, A.SOUTH)

    assert state.agent_1 == (2, 3)
    assert state.agent_2 == (1, 3)
    assert state.boxes == frozenset({(2, 4)})
    assert state.step_count == 1

    assert engine.last_conflict is not None
    assert engine.last_conflict["type"] == "same_box"
    assert engine.last_conflict["p"] == 0.49
    assert engine.last_conflict["winner"] == 1
    assert engine.last_conflict["loser"] == 2

    print("Cùng đẩy một thùng, p < 0.5, Agent 1 thắng: PASS")

    # p >= 0.5: Agent 2 đẩy thùng xuống dưới.
    engine = make_engine(same_box_layout)

    with patch(
        "competitive.game_engine.random.random",
        return_value=0.50,
    ):
        state = engine.step(A.EAST, A.SOUTH)

    assert state.agent_1 == (2, 2)
    assert state.agent_2 == (2, 3)
    assert state.boxes == frozenset({(3, 3)})
    assert state.step_count == 1

    assert engine.last_conflict is not None
    assert engine.last_conflict["type"] == "same_box"
    assert engine.last_conflict["p"] == 0.50
    assert engine.last_conflict["winner"] == 2
    assert engine.last_conflict["loser"] == 1

    print("Cùng đẩy một thùng, p >= 0.5, Agent 2 thắng: PASS")

    # 6. Các xung đột vật lý khác vẫn hủy toàn bộ lượt.
    conflict_cases = [
        (
            "Hai agent đổi chỗ",
            "%%%%%%%\n%12   %\n% B D %\n%%%%%%%\n",
            A.EAST,
            A.WEST,
        ),
        (
            "Hai thùng cùng tới một ô",
            "%%%%%%%\n%1B B2%\n% D D %\n%%%%%%%\n",
            A.EAST,
            A.WEST,
        ),
        (
            "Agent và thùng cùng tới một ô",
            "%%%%%%%%\n%1B 2  %\n% D    %\n%%%%%%%%\n",
            A.EAST,
            A.WEST,
        ),
        (
            "Đẩy thùng vào agent đứng yên",
            "%%%%%%%\n%1B2 D%\n%     %\n%%%%%%%\n",
            A.EAST,
            A.WAIT,
        ),
    ]

    for name, layout, action_1, action_2 in conflict_cases:
        engine = make_engine(layout)
        assert_cancelled(engine, action_1, action_2)
        print(f"{name}: PASS")

    # 5. Agent 1 đi vào ô agent 2 vừa rời đi.
    engine = make_engine(
        "%%%%%%%\n"
        "%12   %\n"
        "% B D %\n"
        "%%%%%%%\n"
    )

    state = engine.step(A.EAST, A.EAST)

    assert state.agent_1 == (1, 2)
    assert state.agent_2 == (1, 3)

    print("Đi vào ô agent kia vừa rời đi: PASS")

    # 6. Kiểm tra đổi quyền sở hữu bằng các hành động thật.
    engine = make_engine(
        "%%%%%%%\n"
        "%1BD 2%\n"
        "%     %\n"
        "%%%%%%%\n",
        max_steps=9,
    )

    # Lượt 1: agent 1 đưa thùng lên đích.
    state = engine.step(A.EAST, A.WAIT)

    assert state.scores == (1, 0)
    assert state.owner_of((1, 3)) == 1
    assert not engine.is_finished()

    # Lượt 2: agent 1 đi xuống, agent 2 tới bên phải thùng.
    engine.step(A.SOUTH, A.WEST)

    # Lượt 3: agent 2 đẩy thùng ra khỏi đích.
    state = engine.step(A.WAIT, A.WEST)

    assert state.scores == (0, 0)
    assert state.owner_of((1, 2)) == 0

    # Lượt 4-9: agent 2 đi vòng sang trái rồi đẩy thùng lên đích.
    remaining_actions = [
        (A.EAST, A.WAIT),
        (A.EAST, A.SOUTH),
        (A.WAIT, A.WEST),
        (A.WAIT, A.WEST),
        (A.WAIT, A.NORTH),
        (A.WAIT, A.EAST),
    ]

    for action_1, action_2 in remaining_actions:
        engine.step(action_1, action_2)

    assert engine.state.step_count == 9
    assert engine.state.scores == (0, 1)
    assert engine.state.owner_of((1, 3)) == 2
    assert engine.is_finished()
    assert engine.get_winner() == 2

    print("Đẩy thùng khỏi đích rồi giành quyền sở hữu: PASS")

    print("\nTất cả kiểm thử GameEngine đã thành công.")


if __name__ == "__main__":
    main()