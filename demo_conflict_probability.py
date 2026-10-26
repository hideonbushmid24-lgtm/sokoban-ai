from pathlib import Path
from tempfile import TemporaryDirectory

from competitive.competitive_map_loader import CompetitiveMapLoader
from competitive.game_engine import Action, CompetitiveGameEngine


def make_engine(layout):
    with TemporaryDirectory() as temp_dir:
        map_path = Path(temp_dir) / "conflict_map.txt"
        map_path.write_text(layout, encoding="utf-8")

        map_data = CompetitiveMapLoader(map_path)

        return CompetitiveGameEngine.from_map_data(
            map_data,
            max_steps=1,
        )


def run_demo(title, layout, action_1, action_2):
    print()
    print("=" * 65)
    print(title)
    print("=" * 65)

    winners = set()

    for trial in range(1, 31):
        engine = make_engine(layout)
        state = engine.step(action_1, action_2)
        conflict = engine.last_conflict

        assert conflict is not None

        p = conflict["p"]
        winner = conflict["winner"]
        loser = conflict["loser"]

        expected_winner = 1 if p < 0.5 else 2

        assert winner == expected_winner
        assert state.step_count == 1

        winners.add(winner)

        print(
            f"Lần {trial:02d}: "
            f"p={p:.6f} -> "
            f"Agent {winner} hành động, "
            f"Agent {loser} đứng yên và mất lượt"
        )

        # Dừng sau khi đã quan sát được cả hai kết quả.
        if winners == {1, 2}:
            break

    print("Các agent đã thắng:", sorted(winners))

    if winners == {1, 2}:
        print("Kết quả minh họa: PASS")
    else:
        print(
            "Chưa quan sát đủ hai kết quả trong 30 lần; "
            "hãy chạy lại demo."
        )


def main():
    same_position_layout = (
        "%%%%%%%\n"
        "% 1 2 %\n"
        "% B D %\n"
        "%%%%%%%\n"
    )

    run_demo(
        "TRƯỜNG HỢP 1: HAI AGENT CÙNG ĐI VÀO MỘT VỊ TRÍ",
        same_position_layout,
        Action.EAST,
        Action.WEST,
    )

    same_box_layout = (
        "%%%%%%%\n"
        "%  2  %\n"
        "% 1B D%\n"
        "%     %\n"
        "%%%%%%%\n"
    )

    run_demo(
        "TRƯỜNG HỢP 2: HAI AGENT CÙNG ĐẨY MỘT THÙNG",
        same_box_layout,
        Action.EAST,
        Action.SOUTH,
    )

    print()
    print("TẤT CẢ DEMO XUNG ĐỘT ĐÃ HOÀN THÀNH.")


if __name__ == "__main__":
    main()