import argparse
from pathlib import Path

from core.map_loader import MapLoader
from core.state import State
from search.astar import AStar
from search.ucs import UCS


BASE_DIR = Path(__file__).resolve().parent


def resolve_map_path(value):
    map_path = Path(value)

    if not map_path.is_absolute():
        map_path = BASE_DIR / map_path

    return map_path.resolve()


def main():
    parser = argparse.ArgumentParser(
        description="Giải bài toán Sokoban bằng UCS hoặc A*."
    )

    parser.add_argument(
        "--map",
        required=True,
        help="Đường dẫn đến file bản đồ Sokoban.",
    )

    parser.add_argument(
        "--algorithm",
        choices=("ucs", "astar"),
        default="astar",
        help="Thuật toán tìm kiếm: ucs hoặc astar.",
    )

    args = parser.parse_args()
    map_path = resolve_map_path(args.map)

    try:
        map_data = MapLoader(map_path)
        initial_state = State.from_map_data(map_data)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    solver = UCS() if args.algorithm == "ucs" else AStar()
    result = solver.solve(initial_state)

    print("=" * 60)
    print("SOKOBAN SOLVER")
    print("=" * 60)
    print(f"Bản đồ: {map_path}")
    print(f"Thuật toán: {args.algorithm.upper()}")
    print(f"Có lời giải: {'Có' if result['solved'] else 'Không'}")
    print(f"Danh sách hành động: {result['actions']}")
    print(f"Tổng chi phí: {result['cost']}")
    print(f"Số hành động: {len(result['actions'])}")
    print(f"Node mở rộng: {result['nodes_expanded']}")
    print(f"Node được sinh: {result['nodes_generated']}")
    print(f"Frontier lớn nhất: {result['max_frontier']}")
    print(
        "Thời gian: "
        f"{result['time_seconds'] * 1000:.3f} ms"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())