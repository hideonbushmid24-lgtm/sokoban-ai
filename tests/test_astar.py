from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

from core.map_loader import MapLoader
from core.state import State
from search.astar import AStar
from search.ucs import UCS


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def check_solution(initial_state, result):
    """Thực hiện lại lời giải để kiểm tra tính hợp lệ."""
    current = initial_state
    states = [current]

    for action in result["actions"]:
        next_state = current.move(action)

        assert next_state is not None, (
            f"Hành động không hợp lệ: {action}"
        )

        current = next_state
        states.append(current)

    assert current.is_goal()
    assert states == result["states"]
    assert result["cost"] == len(result["actions"])


def main():
    astar = AStar()
    ucs = UCS()

    test_cases = [
        ("map_01_tiny.txt", True, 1),
        ("map_02_small.txt", True, 13),
        ("map_03_blocked.txt", False, None),
    ]

    for filename, expected_solved, expected_cost in test_cases:
        map_data = MapLoader(MAPS_DIR / filename)
        initial_state = State.from_map_data(map_data)

        result = astar.solve(initial_state)
        ucs_result = ucs.solve(initial_state)

        assert result["solved"] == expected_solved
        assert result["cost"] == expected_cost

        # Hai thuật toán phải thống nhất kết quả và chi phí.
        assert result["solved"] == ucs_result["solved"]
        assert result["cost"] == ucs_result["cost"]

        print(f"\n=== {filename} ===")

        if result["solved"]:
            check_solution(initial_state, result)

            print("Actions:", result["actions"])
            print("Total cost:", result["cost"])
        else:
            assert result["actions"] == []
            assert result["states"] == []

            print("Không tìm thấy lời giải.")
            print("Total cost:", result["cost"])

        print("A* nodes expanded:", result["nodes_expanded"])
        print("UCS nodes expanded:", ucs_result["nodes_expanded"])
        print("A* nodes generated:", result["nodes_generated"])
        print("A* max frontier:", result["max_frontier"])
        print(f"A* time: {result['time_seconds']:.6f} giây")
        print("Kết quả: PASS")

    # Trạng thái hoàn thành ngay từ đầu.
    tiny = State.from_map_data(
        MapLoader(MAPS_DIR / "map_01_tiny.txt")
    )

    completed = replace(tiny, boxes=tiny.goals)
    result = astar.solve(completed)

    assert result["solved"]
    assert result["cost"] == 0
    assert result["actions"] == []
    assert result["states"] == [completed]
    assert result["nodes_expanded"] == 0

    print("\nTrạng thái hoàn thành ngay từ đầu: PASS")

    # Thùng và đích ở hai vùng bị ngăn cách bởi tường.
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "disconnected.txt"
        path.write_text(
            "%%%%%%\n"
            "%AD%B%\n"
            "%%%%%%\n",
            encoding="utf-8",
        )

        state = State.from_map_data(MapLoader(path))
        result = astar.solve(state)

        assert not result["solved"]
        assert result["cost"] is None
        assert result["actions"] == []
        assert result["states"] == []
        assert result["nodes_expanded"] == 0

    print("Phát hiện trường hợp heuristic vô cùng: PASS")
    print("Tất cả kiểm thử A* đã thành công.")


if __name__ == "__main__":
    main()