import csv

from collections import deque
from math import inf
from pathlib import Path

from core.map_loader import MapLoader
from core.state import State
from search.heuristic import Heuristic


BASE_DIR = Path(__file__).resolve().parent
MAPS_DIR = BASE_DIR / "maps"
RESULTS_DIR = BASE_DIR / "results"

MAP_FILES = [
    "map_01_tiny.txt",
    "map_02_small.txt",
    "map_03_blocked.txt",
]

# Giới hạn bảo vệ khi vô tình chọn bản đồ quá lớn.
MAX_STATES = 50000


def build_reverse_graph(initial_state):
    """
    Duyệt mọi trạng thái có thể đi tới từ trạng thái ban đầu.

    reverse_edges[next_state] chứa những trạng thái có thể
    thực hiện một hành động hợp lệ để đến next_state.
    """
    reverse_edges = {initial_state: []}
    queue = deque([initial_state])
    edge_count = 0

    while queue:
        current = queue.popleft()

        for _, next_state, step_cost in current.get_successors():
            if step_cost != 1:
                raise ValueError(
                    "Phép kiểm chứng này yêu cầu mọi bước có chi phí 1."
                )

            if next_state not in reverse_edges:
                if len(reverse_edges) >= MAX_STATES:
                    raise RuntimeError(
                        f"Vượt giới hạn {MAX_STATES} trạng thái. "
                        "Chưa duyệt hết nên không thể kết luận "
                        "kiểm chứng đầy đủ. Hãy dùng bản đồ nhỏ hơn."
                    )

                reverse_edges[next_state] = []
                queue.append(next_state)

            reverse_edges[next_state].append(current)
            edge_count += 1

    return reverse_edges, edge_count


def calculate_exact_costs(reverse_edges):
    """
    Tính h*(s) bằng BFS ngược từ tất cả trạng thái hoàn thành.

    Trạng thái không xuất hiện trong exact_cost là trạng thái
    không thể đi đến bất kỳ trạng thái hoàn thành nào.
    """
    goal_states = [
        state
        for state in reverse_edges
        if state.is_goal()
    ]

    exact_cost = {state: 0 for state in goal_states}
    queue = deque(goal_states)

    while queue:
        current = queue.popleft()

        for previous in reverse_edges[current]:
            if previous not in exact_cost:
                exact_cost[previous] = exact_cost[current] + 1
                queue.append(previous)

    return exact_cost, goal_states


def validate_map(filename):
    map_data = MapLoader(MAPS_DIR / filename)
    initial_state = State.from_map_data(map_data)

    reverse_edges, edge_count = build_reverse_graph(initial_state)

    exact_cost, goal_states = calculate_exact_costs(reverse_edges)

    heuristic = Heuristic(initial_state)

    # Tính heuristic một lần cho mỗi trạng thái.
    estimates = {
        state: heuristic.estimate(state)
        for state in reverse_edges
    }

    # 1. Kiểm tra h(s) <= h*(s).
    admissibility_violations = sum(
        estimates[state] > exact_cost.get(state, inf)
        for state in reverse_edges
    )

    # 2. Kiểm tra h(s) <= 1 + h(s') trên từng cạnh s -> s'.
    consistency_violations = 0

    for next_state, previous_states in reverse_edges.items():
        for previous in previous_states:
            if estimates[previous] > 1 + estimates[next_state]:
                consistency_violations += 1

    # 3. Kiểm tra h(goal) = 0.
    goal_violations = sum(
        estimates[state] != 0
        for state in goal_states
    )

    reachable_states = len(reverse_edges)
    solvable_states = len(exact_cost)

    passed = (
        admissibility_violations == 0
        and consistency_violations == 0
        and goal_violations == 0
    )

    return {
        "map": filename,
        "reachable_states": reachable_states,
        "edges": edge_count,
        "goal_states": len(goal_states),
        "solvable_states": solvable_states,
        "unsolvable_states": reachable_states - solvable_states,
        "initial_h": estimates[initial_state],
        "initial_optimal_cost": exact_cost.get(initial_state, inf),
        "admissibility_violations": admissibility_violations,
        "consistency_violations": consistency_violations,
        "goal_violations": goal_violations,
        "passed": passed,
    }


def save_results(rows):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "heuristic_validation.csv"

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)

    return output_path


def main():
    rows = []

    for filename in MAP_FILES:
        print(f"\n=== {filename} ===")
        print("Đang duyệt toàn bộ trạng thái có thể đi tới...")

        result = validate_map(filename)
        rows.append(result)

        print("Số trạng thái:", result["reachable_states"])
        print("Số cạnh:", result["edges"])
        print("Trạng thái hoàn thành:", result["goal_states"])
        print("Trạng thái còn giải được:", result["solvable_states"])
        print("Trạng thái không giải được:", result["unsolvable_states"])

        print("h ban đầu:", result["initial_h"])
        print("Chi phí tối ưu ban đầu:", result["initial_optimal_cost"])

        print(
            "Vi phạm admissibility:",
            result["admissibility_violations"],
        )
        print(
            "Vi phạm consistency:",
            result["consistency_violations"],
        )
        print("Vi phạm h(goal) = 0:", result["goal_violations"])

        status = "PASS" if result["passed"] else "FAIL"
        print("Kết quả:", status)

    output_path = save_results(rows)
    print(f"\nĐã lưu kết quả tại: {output_path}")

    if not all(row["passed"] for row in rows):
        raise AssertionError(
            "Phát hiện vi phạm. Hãy kiểm tra heuristic và state."
        )

    print("Tất cả kiểm chứng Heuristic đã thành công.")


if __name__ == "__main__":
    main()