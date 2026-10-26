from heapq import heappush, heappop
from itertools import count
from math import inf
from time import perf_counter

from core.node import Node
from search.heuristic import Heuristic


class AStar:
    """A* với heuristic khoảng cách BFS và ghép thùng - đích."""

    def solve(self, initial_state):
        start_time = perf_counter()

        # Tạo heuristic riêng cho mỗi lần giải.
        heuristic = Heuristic(initial_state)

        root = Node(state=initial_state)
        root_h = heuristic.estimate(initial_state)

        order = count()
        frontier = []

        # Nếu không thể ghép thùng với đích ngay trong bài toán
        # đơn giản hóa, bản đồ thực tế cũng không có lời giải.
        if root_h != inf:
            heappush(frontier, (root_h, next(order), root))

        # Lưu g(n) tốt nhất, không phải f(n).
        best_cost = {initial_state: 0}

        nodes_expanded = 0
        nodes_generated = 1
        max_frontier = len(frontier)

        goal_node = None

        while frontier:
            _, _, current = heappop(frontier)

            # Bỏ qua node cũ nếu đã có đường đi rẻ hơn.
            if current.path_cost != best_cost[current.state]:
                continue

            # Kiểm tra mục tiêu khi lấy node ra khỏi hàng đợi.
            if current.state.is_goal():
                goal_node = current
                break

            nodes_expanded += 1

            for child in current.expand():
                nodes_generated += 1

                old_cost = best_cost.get(child.state, inf)

                if child.path_cost >= old_cost:
                    continue

                child_h = heuristic.estimate(child.state)

                # Loại trạng thái chắc chắn không thể giải.
                if child_h == inf:
                    continue

                best_cost[child.state] = child.path_cost

                # f(n) = g(n) + h(n).
                priority = child.path_cost + child_h

                heappush(
                    frontier,
                    (
                        priority,
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