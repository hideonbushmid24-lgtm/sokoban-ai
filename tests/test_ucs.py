from dataclasses import replace
from pathlib import Path

from core.map_loader import MapLoader
from core.state import State
from search.ucs import UCS


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def check_solution(initial_state, result):
    """Phát lại hành động để xác nhận lời giải thực sự hợp lệ."""
    current = initial_state
    states = [current]

    for action in result["actions"]:
        next_state = current.move(action)

        assert next_state is not None, (
            f"Lời giải chứa hành động không hợp lệ: {action}"
        )

        current = next_state
        states.append(current)

    assert current.is_goal()
    assert states == result["states"]

    # Mỗi hành động có chi phí 1.
    assert result["cost"] == len(result["actions"])


def main():
    solver = UCS()

    test_cases = [
        ("map_01_tiny.txt", True, 1),
        ("map_02_small.txt", True, 13),
        ("map_03_blocked.txt", False, None),
    ]

    for filename, expected_solved, expected_cost in test_cases:
        map_data = MapLoader(MAPS_DIR / filename)
        initial_state = State.from_map_data(map_data)

        result = solver.solve(initial_state)

        assert result["solved"] == expected_solved
        assert result["cost"] == expected_cost

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

        print("Nodes expanded:", result["nodes_expanded"])
        print("Nodes generated:", result["nodes_generated"])
        print("Max frontier:", result["max_frontier"])
        print(f"Time: {result['time_seconds']:.6f} giây")
        print("Kết quả: PASS")

    # Kiểm tra trạng thái đã hoàn thành ngay từ đầu.
    map_data = MapLoader(MAPS_DIR / "map_01_tiny.txt")
    initial_state = State.from_map_data(map_data)

    completed_state = replace(
        initial_state,
        boxes=initial_state.goals,
    )

    result = solver.solve(completed_state)

    assert result["solved"]
    assert result["cost"] == 0
    assert result["actions"] == []
    assert result["states"] == [completed_state]
    assert result["nodes_expanded"] == 0

    print("\nTrạng thái hoàn thành ngay từ đầu: PASS")
    print("Tất cả kiểm thử UCS đã thành công.")


if __name__ == "__main__":
    main()