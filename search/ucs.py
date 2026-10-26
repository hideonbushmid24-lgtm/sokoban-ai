from heapq import heappush, heappop
from itertools import count
from time import perf_counter

from core.node import Node


class UCS:
    """Uniform Cost Search: tìm lời giải có tổng chi phí nhỏ nhất."""

    def solve(self, initial_state):
        start_time = perf_counter()

        root = Node(state=initial_state)

        # Phân biệt các node có cùng chi phí.
        # Nhờ đó heap không phải so sánh trực tiếp hai đối tượng Node.
        order = count()

        # Hàng đợi ưu tiên:
        # (tổng chi phí, thứ tự thêm vào, node).
        frontier = []
        heappush(frontier, (0, next(order), root))

        # Chi phí tốt nhất đã tìm thấy để đến mỗi trạng thái.
        best_cost = {initial_state: 0}

        nodes_expanded = 0
        nodes_generated = 1  # Tính cả node gốc.
        max_frontier = 1

        goal_node = None

        while frontier:
            _, _, current = heappop(frontier)

            # Bỏ qua node cũ nếu đã có đường đến trạng thái này rẻ hơn.
            if current.path_cost != best_cost[current.state]:
                continue

            # Kiểm tra mục tiêu khi lấy node ra khỏi hàng đợi.
            if current.state.is_goal():
                goal_node = current
                break

            nodes_expanded += 1

            for child in current.expand():
                nodes_generated += 1

                old_cost = best_cost.get(
                    child.state,
                    float("inf"),
                )

                # Chỉ thêm vào hàng đợi nếu tìm được chi phí tốt hơn.
                if child.path_cost < old_cost:
                    best_cost[child.state] = child.path_cost

                    heappush(
                        frontier,
                        (
                            child.path_cost,
                            next(order),
                            child,
                        ),
                    )

            max_frontier = max(max_frontier, len(frontier))

        elapsed = perf_counter() - start_time

        return {
            "solved": goal_node is not None,
            "actions": (
                goal_node.get_actions()
                if goal_node is not None
                else []
            ),
            "states": (
                goal_node.get_states()
                if goal_node is not None
                else []
            ),
            "cost": (
                goal_node.path_cost
                if goal_node is not None
                else None
            ),
            "nodes_expanded": nodes_expanded,
            "nodes_generated": nodes_generated,
            "max_frontier": max_frontier,
            "time_seconds": elapsed,
        }