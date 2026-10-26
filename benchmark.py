import csv
import gc
import tracemalloc

from pathlib import Path
from statistics import median
from time import perf_counter

from core.map_loader import MapLoader
from core.state import State
from search.ucs import UCS
from search.astar import AStar


BASE_DIR = Path(__file__).resolve().parent
MAPS_DIR = BASE_DIR / "maps"
RESULTS_DIR = BASE_DIR / "results"

MAP_FILES = [
    "map_01_tiny.txt",
    "map_02_small.txt",
    "map_03_blocked.txt",
]

# Mỗi thuật toán được đo thời gian 5 lần trên mỗi bản đồ.
REPEATS = 5


def benchmark_solver(solver_class, initial_state):
    """Đo thời gian và bộ nhớ riêng biệt."""
    time_samples = []
    summary = None

    # 1. Đo thời gian, không bật theo dõi bộ nhớ.
    for _ in range(REPEATS):
        gc.collect()
        solver = solver_class()

        start = perf_counter()
        result = solver.solve(initial_state)
        elapsed = perf_counter() - start

        time_samples.append(elapsed * 1000)

        current_summary = {
            "solved": result["solved"],
            "cost": result["cost"],
            "nodes_expanded": result["nodes_expanded"],
            "nodes_generated": result["nodes_generated"],
            "max_frontier": result["max_frontier"],
        }

        # Các lần chạy phải thống nhất khả năng giải và chi phí.
        if summary is not None:
            if (
                current_summary["solved"] != summary["solved"]
                or current_summary["cost"] != summary["cost"]
            ):
                raise RuntimeError(
                    "Kết quả không nhất quán giữa các lần chạy."
                )

        summary = current_summary

        # Không giữ chuỗi trạng thái của lần chạy trước.
        del result

    # 2. Đo bộ nhớ bằng một lượt chạy riêng.
    gc.collect()
    solver = solver_class()

    tracemalloc.start()

    try:
        memory_result = solver.solve(initial_state)
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    if (
        memory_result["solved"] != summary["solved"]
        or memory_result["cost"] != summary["cost"]
    ):
        raise RuntimeError(
            "Lượt đo bộ nhớ cho kết quả khác lượt đo thời gian."
        )

    del memory_result

    summary["repeats"] = REPEATS
    summary["time_ms_median"] = round(median(time_samples), 3)
    summary["peak_python_kib"] = round(peak_bytes / 1024, 3)

    return summary


def save_csv(rows):
    """Lưu kết quả để sử dụng trong báo cáo."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "benchmark.csv"

    fieldnames = [
        "map",
        "algorithm",
        "solved",
        "cost",
        "nodes_expanded",
        "nodes_generated",
        "max_frontier",
        "repeats",
        "time_ms_median",
        "peak_python_kib",
    ]

    # UTF-8 có BOM giúp Excel đọc tiếng Việt thuận tiện hơn.
    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def print_results(rows):
    print("\nKẾT QUẢ BENCHMARK")
    print(
        f"{'Map':<20}"
        f"{'Algo':<7}"
        f"{'Solved':<8}"
        f"{'Cost':>6}"
        f"{'Time(ms)':>12}"
        f"{'Peak(KiB)':>12}"
        f"{'Expanded':>11}"
    )
    print("-" * 76)

    for row in rows:
        solved_text = "Yes" if row["solved"] else "No"
        cost_text = (
            str(row["cost"])
            if row["cost"] is not None
            else "-"
        )

        print(
            f"{row['map']:<20}"
            f"{row['algorithm']:<7}"
            f"{solved_text:<8}"
            f"{cost_text:>6}"
            f"{row['time_ms_median']:>12.3f}"
            f"{row['peak_python_kib']:>12.3f}"
            f"{row['nodes_expanded']:>11}"
        )


def main():
    rows = []

    for filename in MAP_FILES:
        print(f"\nĐang kiểm tra: {filename}")

        map_data = MapLoader(MAPS_DIR / filename)
        initial_state = State.from_map_data(map_data)

        map_results = []

        for algorithm_name, solver_class in [
            ("UCS", UCS),
            ("A*", AStar),
        ]:
            print(f"  Đang đo {algorithm_name}...")

            metrics = benchmark_solver(
                solver_class,
                initial_state,
            )

            row = {
                "map": filename,
                "algorithm": algorithm_name,
                **metrics,
            }

            rows.append(row)
            map_results.append(row)

        ucs_result, astar_result = map_results

        if (
            ucs_result["solved"] != astar_result["solved"]
            or ucs_result["cost"] != astar_result["cost"]
        ):
            raise RuntimeError(
                f"UCS và A* cho kết quả khác nhau trên {filename}."
            )

    print_results(rows)

    output_path = save_csv(rows)

    print(f"\nThời gian: trung vị của {REPEATS} lần chạy.")
    print("Bộ nhớ: đỉnh cấp phát Python trong một lượt chạy riêng.")
    print(f"Đã lưu kết quả tại: {output_path}")


if __name__ == "__main__":
    main()