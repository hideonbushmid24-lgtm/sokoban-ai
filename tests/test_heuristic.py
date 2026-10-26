from pathlib import Path
from tempfile import TemporaryDirectory
from math import inf

from core.map_loader import MapLoader
from core.state import State
from search.heuristic import Heuristic


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def load_state(path):
    return State.from_map_data(MapLoader(path))


def main():
    # 1. Kiểm tra ba bản đồ hiện tại.
    test_cases = [
        ("map_01_tiny.txt", 1),
        ("map_02_small.txt", 4),
        ("map_03_blocked.txt", 4),
    ]

    for filename, expected in test_cases:
        state = load_state(MAPS_DIR / filename)
        heuristic = Heuristic(state)

        value = heuristic.estimate(state)

        assert value == expected

        # Gọi lại để kiểm tra kết quả khi dùng cache.
        assert heuristic.estimate(state) == expected

        print(f"{filename}: h = {value} - PASS")

    # 2. Thùng vào đích thì heuristic bằng 0.
    tiny = load_state(MAPS_DIR / "map_01_tiny.txt")
    heuristic = Heuristic(tiny)

    completed = tiny.move("East")

    assert completed is not None
    assert heuristic.estimate(completed) == 0

    print("Thùng vào đích: h = 0 - PASS")

    # 3. Agent di chuyển, thùng giữ nguyên -> h giữ nguyên.
    small = load_state(MAPS_DIR / "map_02_small.txt")
    heuristic = Heuristic(small)

    moved = small.move("West")

    assert moved is not None
    assert heuristic.estimate(moved) == heuristic.estimate(small)

    print("Agent di chuyển, thùng giữ nguyên: PASS")

    # 4. Các bản đồ tạm phục vụ kiểm thử.
    extra_cases = [
        (
            "Ghép mỗi thùng với một đích khác nhau",
            "%%%%%%%%\n"
            "%DBB  D%\n"
            "%  A   %\n"
            "%%%%%%%%\n",
            4,
        ),
        (
            "BFS tính đường vòng qua tường",
            "%%%%%\n"
            "%D%B%\n"
            "% A %\n"
            "%%%%%\n",
            4,
        ),
        (
            "Thùng và đích bị tường ngăn cách hoàn toàn",
            "%%%%%%\n"
            "%AD%B%\n"
            "%%%%%%\n",
            inf,
        ),
    ]

    with TemporaryDirectory() as temp_dir:
        for index, (name, content, expected) in enumerate(extra_cases):
            path = Path(temp_dir) / f"test_{index}.txt"
            path.write_text(content, encoding="utf-8")

            state = load_state(path)
            heuristic = Heuristic(state)

            value = heuristic.estimate(state)

            assert value == expected

            print(f"{name}: h = {value} - PASS")

    print("\nTất cả kiểm thử Heuristic đã thành công.")


if __name__ == "__main__":
    main()