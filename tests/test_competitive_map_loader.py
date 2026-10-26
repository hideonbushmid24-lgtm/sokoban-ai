from pathlib import Path
from tempfile import TemporaryDirectory

from competitive.competitive_map_loader import CompetitiveMapLoader


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def main():
    # 1. Kiểm tra bản đồ chính.
    map_data = CompetitiveMapLoader(
        MAPS_DIR / "map_competitive_test.txt"
    )

    assert (map_data.rows, map_data.cols) == (7, 9)

    assert map_data.agent_1 == (3, 3)
    assert map_data.agent_2 == (3, 5)

    assert map_data.agents == {
        1: (3, 3),
        2: (3, 5),
    }

    assert map_data.boxes == {(2, 3), (2, 5)}
    assert map_data.goals == {(1, 3), (1, 5)}

    assert map_data.box_owners == {
        (2, 3): 0,
        (2, 5): 0,
    }

    assert map_data.is_floor(map_data.agent_1)
    assert map_data.is_floor(map_data.agent_2)
    assert not map_data.is_floor((0, 0))
    assert not map_data.is_floor((-1, 0))

    print("=== BẢN ĐỒ COMPETITIVE ===")
    map_data.display()

    print(f"Kích thước: {map_data.rows} x {map_data.cols}")
    print("Agent 1:", map_data.agent_1)
    print("Agent 2:", map_data.agent_2)
    print("Thùng:", sorted(map_data.boxes))
    print("Đích:", sorted(map_data.goals))
    print("Đọc bản đồ chính: PASS")

    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        # 2. C vừa là thùng vừa là đích, ban đầu trung lập.
        c_path = temp_dir / "map_with_c.txt"
        c_path.write_text(
            "%%%%%%\n"
            "%1C 2%\n"
            "%%%%%%\n",
            encoding="utf-8",
        )

        c_map = CompetitiveMapLoader(c_path)

        assert c_map.boxes == {(1, 2)}
        assert c_map.goals == {(1, 2)}
        assert c_map.box_owners[(1, 2)] == 0

        print("Ký hiệu C và quyền sở hữu ban đầu: PASS")

        # 3. Các trường hợp định dạng sai.
        invalid_cases = [
            (
                "Thiếu agent 2",
                "%%%%%%\n"
                "%1BD %\n"
                "%%%%%%\n",
            ),
            (
                "Trùng agent 1",
                "%%%%%%%\n"
                "%11BD2%\n"
                "%%%%%%%\n",
            ),
            (
                "Các dòng không cùng độ dài",
                "%%%%%%\n"
                "%1BD2%\n"
                "%%%%%\n",
            ),
            (
                "Ký hiệu không hợp lệ",
                "%%%%%%\n"
                "%1@D2%\n"
                "%%%%%%\n",
            ),
        ]

        for index, (name, content) in enumerate(invalid_cases):
            path = temp_dir / f"invalid_{index}.txt"
            path.write_text(content, encoding="utf-8")

            try:
                CompetitiveMapLoader(path)
            except ValueError:
                print(f"Phát hiện lỗi '{name}': PASS")
            else:
                raise AssertionError(
                    f"Loader chưa phát hiện lỗi: {name}"
                )

    print("\nTất cả kiểm thử CompetitiveMapLoader đã thành công.")


if __name__ == "__main__":
    main()