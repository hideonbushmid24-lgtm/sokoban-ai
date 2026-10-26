from pathlib import Path

from core.map_loader import MapLoader
from core.state import State
from core.node import Node


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def main():
    map_data = MapLoader(MAPS_DIR / "map_01_tiny.txt")
    initial_state = State.from_map_data(map_data)

    # 1. Node gốc chưa thực hiện hành động nào.
    root = Node(state=initial_state)

    assert root.parent is None
    assert root.action is None
    assert root.path_cost == 0
    assert root.depth == 0
    assert root.get_actions() == []
    assert root.get_states() == [initial_state]

    print("1. Khởi tạo node gốc: PASS")

    # 2. Tiny chỉ có một hành động hợp lệ: East.
    children = root.expand()

    assert len(children) == 1

    goal_node = children[0]

    assert goal_node.parent is root
    assert goal_node.action == "East"
    assert goal_node.path_cost == 1
    assert goal_node.depth == 1
    assert goal_node.state.is_goal()

    print("2. Sinh node con và cộng chi phí: PASS")

    # 3. Truy ngược lời giải.
    assert goal_node.get_actions() == ["East"]
    assert goal_node.get_states() == [
        initial_state,
        goal_node.state,
    ]

    print("3. Truy ngược hành động và trạng thái: PASS")

    # 4. Kiểm tra truy ngược một đường đi nhiều bước.
    # Sau East, agent đi West rồi East.
    # Đây chỉ là đường đi dùng để test, không phải lời giải tối ưu.
    back_node = next(
        child
        for child in goal_node.expand()
        if child.action == "West"
    )

    forward_node = next(
        child
        for child in back_node.expand()
        if child.action == "East"
    )

    assert forward_node.get_actions() == ["East", "West", "East"]
    assert forward_node.path_cost == 3
    assert forward_node.depth == 3

    assert forward_node.get_states() == [
        root.state,
        goal_node.state,
        back_node.state,
        forward_node.state,
    ]

    # Việc mở rộng không làm thay đổi node gốc.
    assert root.path_cost == 0
    assert root.state.player == (1, 1)

    print("4. Truy ngược đường đi nhiều bước: PASS")

    print("\nLời giải của map tiny:")
    print("Actions:", goal_node.get_actions())
    print("Total cost:", goal_node.path_cost)

    print("\nTất cả kiểm thử Node đã thành công.")


if __name__ == "__main__":
    main()