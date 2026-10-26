from dataclasses import replace
from pathlib import Path

from competitive.competitive_map_loader import CompetitiveMapLoader
from competitive.competitive_state import CompetitiveState


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def main():
    map_data = CompetitiveMapLoader(
        MAPS_DIR / "map_competitive_test.txt"
    )

    initial = CompetitiveState.from_map_data(map_data)

    # 1. Trạng thái ban đầu.
    assert initial.agent_1 == (3, 3)
    assert initial.agent_2 == (3, 5)
    assert initial.step_count == 0
    assert initial.scores == (0, 0)
    assert initial.neutral_boxes == initial.boxes

    assert initial.owner_of((2, 3)) == 0
    assert initial.owner_of((0, 0)) is None
    assert initial.winner(10) is None

    print("1. Trạng thái ban đầu: PASS")

    # 2. Dựng trạng thái sau khi cả hai cùng đẩy North.
    completed = initial.next_state(
        agent_1=(2, 3),
        agent_2=(2, 5),
        boxes={(1, 3), (1, 5)},
        box_owners={
            (1, 3): 1,
            (1, 5): 2,
        },
    )

    assert completed.step_count == 1
    assert completed.scores == (1, 1)
    assert completed.owner_of((1, 3)) == 1
    assert completed.owner_of((1, 5)) == 2
    assert completed.all_boxes_on_goals()

    print("2. Hai agent ghi điểm trong cùng một lượt: PASS")

    # 3. Đủ thùng trên đích chưa có nghĩa là hết trận.
    assert not completed.is_terminal(10)
    assert completed.winner(10) is None

    # Nếu giới hạn chỉ là 1 lượt thì trận đã kết thúc và hòa.
    assert completed.is_terminal(1)
    assert completed.winner(1) == 0

    print("3. Kết thúc đúng giới hạn lượt: PASS")

    # 4. Dựng một tình huống ở lượt 4:
    # thùng của agent 1 đã bị đưa ra khỏi đích.
    # Đây là dữ liệu kiểm thử, chưa mô phỏng chuỗi hành động.
    released = replace(
        completed,
        agent_1=(1, 3),
        boxes=frozenset({(1, 4), (1, 5)}),
        box_owners=frozenset({
            ((1, 4), 0),
            ((1, 5), 2),
        }),
        step_count=4,
    )

    assert released.scores == (0, 1)
    assert released.owner_of((1, 4)) == 0
    assert released.winner(4) == 2

    print("4. Thùng ra khỏi đích và mất điểm: PASS")

    # 5. Tình huống agent 2 sở hữu cả hai thùng trên đích.
    reclaimed = replace(
        completed,
        box_owners=frozenset({
            ((1, 3), 2),
            ((1, 5), 2),
        }),
        step_count=7,
    )

    assert reclaimed.scores == (0, 2)
    assert reclaimed.winner(7) == 2

    print("5. Tính điểm khi quyền sở hữu thay đổi: PASS")

    # 6. Các trạng thái trước đó không bị thay đổi.
    assert initial.step_count == 0
    assert initial.scores == (0, 0)
    assert completed.scores == (1, 1)

    same_initial = CompetitiveState.from_map_data(map_data)
    assert len({initial, same_initial}) == 1

    print("6. Trạng thái bất biến và dùng được trong set: PASS")

    # 7. Không cho phép hai agent đứng trùng nhau.
    try:
        replace(initial, agent_2=initial.agent_1)
    except ValueError:
        print("7. Phát hiện hai agent trùng vị trí: PASS")
    else:
        raise AssertionError("Chưa phát hiện agent trùng vị trí.")

    # 8. Thùng ngoài đích không được mang quyền sở hữu 1 hoặc 2.
    try:
        replace(
            initial,
            box_owners=frozenset({
                ((2, 3), 1),
                ((2, 5), 0),
            }),
        )
    except ValueError:
        print("8. Phát hiện quyền sở hữu không hợp lệ: PASS")
    else:
        raise AssertionError("Chưa phát hiện quyền sở hữu sai.")

    print("\nTất cả kiểm thử CompetitiveState đã thành công.")


if __name__ == "__main__":
    main()