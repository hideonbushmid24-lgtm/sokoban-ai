import multiprocessing as mp
from time import perf_counter

from competitive.game_engine import Action, CompetitiveGameEngine


def _agent_worker(connection, agent):
    """
    Chạy agent trong tiến trình riêng.

    Hàm phải nằm ở cấp module để hoạt động với multiprocessing
    trên Windows.
    """
    try:
        connection.send("ready")

        while True:
            request = connection.recv()

            if request is None:
                break

            state, remaining_steps = request
            start = perf_counter()

            try:
                action = Action(
                    agent.choose_action(
                        state,
                        remaining_steps=remaining_steps,
                    )
                )

                response = {
                    "action": action,
                    "status": "ok",
                    "error": "",
                    "stats": dict(
                        getattr(agent, "last_stats", {})
                    ),
                }

            except Exception as exc:
                response = {
                    "action": Action.WAIT,
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                    "stats": {},
                }

            response["compute_ms"] = (
                perf_counter() - start
            ) * 1000

            connection.send(response)

    except (EOFError, BrokenPipeError, OSError):
        pass

    finally:
        connection.close()


class _AgentProcess:
    """Quản lý tiến trình và thời hạn trả lời của một agent."""

    def __init__(self, agent):
        self.agent = agent
        self.context = mp.get_context("spawn")

        self.process = None
        self.connection = None

    def close(self):
        """Dừng tiến trình và giải phóng kết nối."""
        if self.process is not None:
            if self.process.is_alive():
                self.process.terminate()

            self.process.join(timeout=0.5)

            if self.process.is_alive():
                self.process.kill()
                self.process.join()

            self.process.close()
            self.process = None

        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def _start(self):
        """Khởi động tiến trình nếu chưa có hoặc đã bị dừng."""
        if (
            self.process is not None
            and self.process.is_alive()
        ):
            return

        self.close()

        parent, child = self.context.Pipe()

        process = self.context.Process(
            target=_agent_worker,
            args=(child, self.agent),
            daemon=True,
        )

        try:
            process.start()

        except Exception:
            parent.close()
            child.close()
            process.close()
            raise

        child.close()

        self.process = process
        self.connection = parent

        # Tách thời gian khởi động Python khỏi thời gian quyết định.
        if (
            not parent.poll(10)
            or parent.recv() != "ready"
        ):
            raise RuntimeError(
                "Không khởi động được tiến trình agent."
            )

    @staticmethod
    def _fallback(status, error, time_ms=0.0):
        """Kết quả thay thế khi agent không trả lời hợp lệ."""
        return {
            "action": Action.WAIT,
            "status": status,
            "error": error,
            "time_ms": time_ms,
            "compute_ms": None,
            "stats": {},
        }

    def choose(self, state, remaining_steps, time_limit_ms):
        try:
            self._start()

        except Exception as exc:
            self.close()

            return self._fallback(
                "startup_error",
                str(exc),
            )

        start = perf_counter()
        deadline = start + time_limit_ms / 1000

        try:
            self.connection.send(
                (state, remaining_steps)
            )

            remaining_time = max(
                0.0,
                deadline - perf_counter(),
            )

            if not self.connection.poll(remaining_time):
                elapsed = (
                    perf_counter() - start
                ) * 1000

                self.close()

                return self._fallback(
                    "timeout",
                    "Agent vượt thời gian cho phép.",
                    elapsed,
                )

            response = self.connection.recv()

            elapsed = (
                perf_counter() - start
            ) * 1000

            if elapsed > time_limit_ms:
                self.close()

                return self._fallback(
                    "timeout",
                    "Kết quả đến sau thời hạn.",
                    elapsed,
                )

            response["time_ms"] = elapsed
            return response

        except (EOFError, BrokenPipeError, OSError) as exc:
            elapsed = (
                perf_counter() - start
            ) * 1000

            self.close()

            return self._fallback(
                "error",
                str(exc),
                elapsed,
            )


class MatchRunner:
    """Điều khiển trận đấu và lưu lịch sử để phát lại."""

    def __init__(
        self,
        initial_state,
        agent_1=None,
        agent_2=None,
        max_steps=20,
        time_limit_ms=1000,
    ):
        if type(max_steps) is not int or max_steps < 1:
            raise ValueError(
                "max_steps phải là số nguyên dương."
            )

        if not 0 < time_limit_ms <= 1000:
            raise ValueError(
                "time_limit_ms phải trong khoảng (0, 1000]."
            )

        if agent_1 is None:
            from competitive.agent_1 import Agent1

            agent_1 = Agent1(agent_id=1)

        if agent_2 is None:
            from competitive.agent_2 import Agent2

            agent_2 = Agent2(agent_id=2)

        if agent_1.agent_id != 1 or agent_2.agent_id != 2:
            raise ValueError(
                "Hai agent phải có ID lần lượt là 1 và 2."
            )

        self.initial_state = initial_state
        self.agent_1 = agent_1
        self.agent_2 = agent_2

        self.max_steps = max_steps
        self.time_limit_ms = time_limit_ms

    def run(self):
        state = self.initial_state

        states = [state]
        history = []

        workers = [
            _AgentProcess(self.agent_1),
            _AgentProcess(self.agent_2),
        ]

        start = perf_counter()

        try:
            while state.step_count < self.max_steps:
                remaining_steps = (
                    self.max_steps - state.step_count
                )

                # Hai agent nhận cùng trạng thái đầu lượt.
                # Chưa cập nhật bàn cờ giữa hai lần chọn hành động.
                decision_1 = workers[0].choose(
                    state,
                    remaining_steps,
                    self.time_limit_ms,
                )

                decision_2 = workers[1].choose(
                    state,
                    remaining_steps,
                    self.time_limit_ms,
                )

                # Chỉ cập nhật trạng thái sau khi có đủ hai hành động.
                next_state, conflict = CompetitiveGameEngine.resolve_turn(
                    state,
                    decision_1["action"],
                    decision_2["action"],
                )

                history.append({
                    "step": next_state.step_count,
                    "state_before": state,
                    "state_after": next_state,
                    "agent_1": decision_1,
                    "agent_2": decision_2,
                    "scores": next_state.scores,
                    "conflict": conflict,
                })

                state = next_state
                states.append(state)

        finally:
            # Luôn dọn tiến trình, kể cả khi trận đấu gặp lỗi.
            for worker in workers:
                worker.close()

        score_1, score_2 = state.scores

        if score_1 == score_2:
            winner = 0
        elif score_1 > score_2:
            winner = 1
        else:
            winner = 2

        return {
            "initial_state": self.initial_state,
            "final_state": state,
            "states": states,
            "history": history,
            "scores": state.scores,
            "winner": winner,
            "steps_played": len(history),
            "time_ms": (
                perf_counter() - start
            ) * 1000,
        }