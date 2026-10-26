from __future__ import annotations

from dataclasses import dataclass

from core.state import State


@dataclass(eq=False)
class Node:
    """Một node trong cây tìm kiếm."""

    state: State
    parent: Node | None = None
    action: str | None = None
    path_cost: int = 0
    depth: int = 0

    def expand(self):
        """Tạo các node con từ những hành động hợp lệ."""
        children = []

        for action, next_state, step_cost in self.state.get_successors():
            child = Node(
                state=next_state,
                parent=self,
                action=action,
                path_cost=self.path_cost + step_cost,
                depth=self.depth + 1,
            )

            children.append(child)

        return children

    def get_actions(self):
        """Lấy danh sách hành động từ node gốc đến node hiện tại."""
        actions = []
        current = self

        while current.parent is not None:
            actions.append(current.action)
            current = current.parent

        # Khi truy ngược, hành động được thu thập từ cuối về đầu.
        actions.reverse()

        return actions

    def get_states(self):
        """
        Lấy các trạng thái từ đầu đến hiện tại.
        Bao gồm cả trạng thái ban đầu, phục vụ phát lại trên GUI.
        """
        states = []
        current = self

        while current is not None:
            states.append(current.state)
            current = current.parent

        states.reverse()

        return states