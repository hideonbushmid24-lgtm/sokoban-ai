import argparse
import multiprocessing as mp
from pathlib import Path

from competitive.competitive_map_loader import CompetitiveMapLoader
from competitive.competitive_state import CompetitiveState
from competitive.match_runner import MatchRunner


BASE_DIR = Path(__file__).resolve().parent


def positive_int(value):
    """Kiểm tra số lượt được nhập."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Số lượt phải là số nguyên."
        )

    if number < 1:
        raise argparse.ArgumentTypeError(
            "Số lượt phải lớn hơn 0."
        )

    return number


def read_steps():
    """Cho người dùng nhập số lượt nếu chưa truyền --steps."""
    while True:
        value = input(
            "Nhập số lượt của trận đấu [mặc định 20]: "
        ).strip()

        if not value:
            return 20

        try:
            return positive_int(value)
        except argparse.ArgumentTypeError as exc:
            print(f"Không hợp lệ: {exc}")


def print_decision(name, decision):
    """In hành động và thông tin xử lý của một agent."""
    status_names = {
        "ok": "Hợp lệ",
        "timeout": "Quá thời gian, dùng Wait",
        "error": "Lỗi agent, dùng Wait",
        "startup_error": "Lỗi khởi động, dùng Wait",
    }

    action = decision["action"].value

    status = status_names.get(
        decision["status"],
        decision["status"],
    )

    print(
        f"  {name}: {action:<5} | "
        f"Thời gian chờ: {decision['time_ms']:.3f} ms | "
        f"{status}"
    )

    stats = decision["stats"]

    if stats:
        print(
            f"    Node mở rộng: "
            f"{stats.get('nodes_expanded', '-')} | "
            f"Lý do: {stats.get('reason', '-')}"
        )

    if decision["error"]:
        print(f"    Chi tiết: {decision['error']}")


def print_result(result):
    """In lịch sử từng lượt và kết quả cuối trận."""
    for turn in result["history"]:
        print(f"\nLượt {turn['step']}:")

        print_decision(
            "Agent1 - BFS",
            turn["agent_1"],
        )

        print_decision(
            "Agent2 - GBFS",
            turn["agent_2"],
        )
        conflict = turn.get("conflict")

        if conflict is None:
            print("  Xung đột: Không")
        else:
            conflict_names = {
                "same_position": "Hai agent cùng vào một vị trí",
                "same_box": "Hai agent cùng đẩy một thùng",
            }

            conflict_name = conflict_names.get(
                conflict["type"],
                conflict["type"],
            )

            print(f"  Xung đột: {conflict_name}")
            print(f"  p = {conflict['p']:.4f}")
            print(
                f"  Agent{conflict['winner']} thắng tranh chấp; "
                f"Agent{conflict['loser']} đứng yên và mất lượt"
            )
        score_1, score_2 = turn["scores"]

        print(
            f"  Điểm hiện tại: "
            f"Agent1 = {score_1} | Agent2 = {score_2}"
        )

    score_1, score_2 = result["scores"]

    winner_names = {
        0: "Hai agent hòa nhau",
        1: "Agent1 - BFS thắng",
        2: "Agent2 - GBFS thắng",
    }

    print("\n=== KẾT QUẢ TRẬN ĐẤU ===")
    print(f"Số lượt đã chơi: {result['steps_played']}")
    print(f"Điểm Agent1 - BFS: {score_1}")
    print(f"Điểm Agent2 - GBFS: {score_2}")
    print(f"Kết quả: {winner_names[result['winner']]}")

    print(
        f"Tổng thời gian chạy: "
        f"{result['time_ms'] / 1000:.3f} giây"
    )

    for key, name in (
        ("agent_1", "Agent1"),
        ("agent_2", "Agent2"),
    ):
        decisions = [
            turn[key]
            for turn in result["history"]
        ]

        timeouts = sum(
            item["status"] == "timeout"
            for item in decisions
        )

        errors = sum(
            item["status"] in ("error", "startup_error")
            for item in decisions
        )

        print(
            f"{name}: {timeouts} lượt quá giờ, "
            f"{errors} lượt lỗi"
        )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Chạy Sokoban Competitive: "
            "Agent1 BFS và Agent2 GBFS."
        )
    )

    parser.add_argument(
        "--map",
        default="maps/map_competitive.txt",
        help=(
            "Đường dẫn bản đồ; đường dẫn tương đối "
            "tính từ thư mục dự án."
        ),
    )

    parser.add_argument(
        "--steps",
        type=positive_int,
        help=(
            "Số lượt của trận đấu. "
            "Nếu bỏ qua, chương trình sẽ hỏi."
        ),
    )

    args = parser.parse_args()

    # Xác định đường dẫn bản đồ.
    map_path = Path(args.map)

    if not map_path.is_absolute():
        map_path = BASE_DIR / map_path

    map_path = map_path.resolve()

    if not map_path.is_file():
        print(f"Không tìm thấy bản đồ: {map_path}")
        return 1

    # Nạp bản đồ và tạo trạng thái ban đầu.
    try:
        map_data = CompetitiveMapLoader(str(map_path))

        initial_state = CompetitiveState.from_map_data(
            map_data
        )

    except (OSError, ValueError) as exc:
        print(f"Không thể nạp bản đồ: {exc}")
        return 1

    steps = (
        args.steps
        if args.steps is not None
        else read_steps()
    )

    print("\n=== SOKOBAN COMPETITIVE ===")
    print(f"Bản đồ: {map_path.name}")
    print(f"Số lượt: {steps}")
    print("Agent1: BFS | Agent2: GBFS")
    print("Thời hạn nhận kết quả: 1000 ms/agent/lượt")

    print(
        "Đang chạy trận đấu; "
        "lịch sử sẽ được in sau khi kết thúc...",
        flush=True,
    )

    runner = MatchRunner(
        initial_state=initial_state,
        max_steps=steps,
        time_limit_ms=1000,
    )

    result = runner.run()

    print_result(result)
    return 0


if __name__ == "__main__":
    mp.freeze_support()

    try:
        raise SystemExit(main())

    except (KeyboardInterrupt, EOFError):
        print("\nĐã dừng chương trình.")
        raise SystemExit(130)