from pathlib import Path
from tempfile import TemporaryDirectory

from core.map_loader import MapLoader


BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "maps"


def main():
    # Tên file, kích thước, agent, thùng, đích mong đợi.
    test_cases = [
        (
            "map_01_tiny.txt",
            (3, 5),
            (1, 1),
            {(1, 2)},
            {(1, 3)},
        ),
        (
            "map_02_small.txt",
            (7, 10),
            (4, 4),
            {(3, 2), (3, 7)},
            {(1, 2), (1, 7)},
        ),
        (
            "map_03_blocked.txt",
            (4, 7),
            (1, 1),
            {(2, 1)},
            {(2, 5)},
        ),
    ]

    for filename, size, player, boxes, goals in test_cases:
        map_data = MapLoader(MAPS_DIR / filename)

        assert (map_data.rows, map_data.cols) == size
        assert map_data.player == player
        assert map_data.boxes == boxes
        assert map_data.goals == goals

        assert map_data.is_floor(player)
        assert not map_data.is_floor((0, 0))
        assert not map_data.is_floor((-1, 0))

        print(f"\n=== {filename} ===")
        map_data.display()
        print(f"Kích thước: {map_data.rows} x {map_data.cols}")
        print(f"Agent: {map_data.player}")
        print(f"Thùng: {sorted(map_data.boxes)}")
        print(f"Đích: {sorted(map_data.goals)}")
        print("Kết quả: PASS")

    # Kiểm tra C được hiểu là thùng nằm trên đích.
    with TemporaryDirectory() as temp_dir:
        temp_map = Path(temp_dir) / "map_with_c.txt"
        temp_map.write_text(
            "%%%%%\n%AC %\n%%%%%\n",
            encoding="utf-8",
        )

        map_data = MapLoader(temp_map)

        assert map_data.boxes == {(1, 2)}
        assert map_data.goals == {(1, 2)}

    print("\nKiểm tra ký hiệu C: PASS")
    print("Tất cả kiểm thử MapLoader đã thành công.")


if __name__ == "__main__":
    main()