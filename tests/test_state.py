from dataclasses import replace
from pathlib import Path

from core.map_loader import MapLoader
from core.state import State


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def load_state(filename):
    map_data = MapLoader(MAPS_DIR / filename)
    return State.from_map_data(map_data)


def main():
    # 1. Kiểm tra trạng thái ban đầu.
    tiny = load_state("map_01_tiny.txt")

    assert tiny.player == (1, 1)
    assert tiny.boxes == frozenset({(1, 2)})
    assert not tiny.is_goal()

    print("1. Trạng thái ban đầu: PASS")

    # 2. Agent không được đi xuyên tường.
    assert tiny.move("North") is None
    assert tiny.move("West") is None
    assert tiny.move("South") is None

    print("2. Chặn agent đi vào tường: PASS")

    # 3. Đẩy thùng sang phải để hoàn thành tiny.
    completed = tiny.move("East")

    assert completed is not None
    assert completed.player == (1, 2)
    assert completed.boxes == frozenset({(1, 3)})
    assert completed.is_goal()

    # Trạng thái cũ phải được giữ nguyên.
    assert tiny.player == (1, 1)
    assert tiny.boxes == frozenset({(1, 2)})

    print("3. Đẩy thùng vào đích, giữ nguyên trạng thái cũ: PASS")

    # 4. Không đẩy thùng vào tường.
    assert completed.move("East") is None

    blocked = load_state("map_03_blocked.txt")
    assert blocked.move("South") is None
    assert not blocked.is_goal()

    print("4. Chặn đẩy thùng vào tường: PASS")

    # 5. Di chuyển trên ô trống.
    small = load_state("map_02_small.txt")
    moved = small.move("West")

    assert moved is not None
    assert moved.player == (4, 3)
    assert moved.boxes == small.boxes

    print("5. Di chuyển trên ô trống: PASS")

    # 6. Tạo tình huống hai thùng đứng liền nhau.
    two_boxes = replace(
        small,
        player=(4, 2),
        boxes=frozenset({(3, 2), (2, 2)}),
    )

    assert two_boxes.move("North") is None

    print("6. Không đẩy hai thùng cùng lúc: PASS")

    # 7. Tiny chỉ có một hành động hợp lệ: East.
    successors = tiny.get_successors()

    assert len(successors) == 1

    action, next_state, cost = successors[0]

    assert action == "East"
    assert next_state.is_goal()
    assert cost == 1

    print("7. Sinh trạng thái kế tiếp và chi phí: PASS")

    # 8. Hai trạng thái giống nhau chỉ chiếm một phần tử trong set.
    same_tiny = load_state("map_01_tiny.txt")

    assert tiny == same_tiny
    assert len({tiny, same_tiny}) == 1

    print("8. Nhận diện trạng thái trùng: PASS")

    print("\nTất cả kiểm thử State đã thành công.")


if __name__ == "__main__":
    main()