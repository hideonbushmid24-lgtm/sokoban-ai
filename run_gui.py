import argparse
from pathlib import Path

from core.map_loader import MapLoader
from gui.game_gui import GameGUI


BASE_DIR = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(
        description="Hiển thị bản đồ Sokoban bằng Pygame."
    )

    parser.add_argument(
        "--map",
        default="maps/map_02_small.txt",
        help="Đường dẫn đến file bản đồ.",
    )

    args = parser.parse_args()

    map_path = Path(args.map)

    # Đường dẫn tương đối được tính từ thư mục dự án.
    if not map_path.is_absolute():
        map_path = BASE_DIR / map_path

    try:
        map_data = MapLoader(map_path)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    gui = GameGUI(map_data)
    gui.run()


if __name__ == "__main__":
    main()