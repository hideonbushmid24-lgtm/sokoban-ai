import argparse
import multiprocessing as mp
from pathlib import Path

from competitive.competitive_map_loader import CompetitiveMapLoader
from competitive.competitive_state import CompetitiveState
from competitive.match_runner import MatchRunner
from run_competitive import positive_int, read_steps


def main():
    parser = argparse.ArgumentParser(
        description="Xem trận đấu Sokoban bằng Pygame."
    )

    parser.add_argument(
        "--map",
        default="maps/map_competitive.txt",
    )

    parser.add_argument(
        "--steps",
        type=positive_int,
    )

    args = parser.parse_args()

    map_path = Path(args.map)

    if not map_path.is_absolute():
        map_path = (
            Path(__file__).resolve().parent
            / map_path
        )

    map_path = map_path.resolve()

    if not map_path.is_file():
        print(f"Không tìm thấy bản đồ: {map_path}")
        return 1

    try:
        data = CompetitiveMapLoader(str(map_path))

        state = CompetitiveState.from_map_data(data)

    except (OSError, ValueError) as exc:
        print(f"Không thể nạp bản đồ: {exc}")
        return 1

    steps = (
        args.steps
        if args.steps is not None
        else read_steps()
    )

    print(
        f"Đang tính trận đấu {steps} lượt. "
        "GUI sẽ mở khi hoàn tất...",
        flush=True,
    )

    result = MatchRunner(
        state,
        max_steps=steps,
    ).run()

    print(f"Điểm cuối trận: {result['scores']}")

    # Chỉ nạp GUI trong tiến trình chính sau khi tính xong.
    from gui.competitive_gui import CompetitiveGUI

    CompetitiveGUI(
        result,
        map_name=map_path.name,
    ).run()

    return 0


if __name__ == "__main__":
    mp.freeze_support()

    try:
        raise SystemExit(main())

    except (KeyboardInterrupt, EOFError):
        print("\nĐã dừng chương trình.")
        raise SystemExit(130)