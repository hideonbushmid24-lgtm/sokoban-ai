# Sokoban AI — UCS, A* and Competitive Agents

Đồ án giữa kỳ môn Nhập môn Trí tuệ nhân tạo.

Dự án giải bài toán Sokoban bằng UCS và A*, đồng thời xây dựng
chế độ thi đấu giữa hai agent sử dụng BFS và GBFS.

## 1. Môi trường khuyến nghị

- Python 3.12.x
- pygame 2.6.1
- Windows 10/11 hoặc macOS 13.7.8 Ventura Intel

## 2. Cài đặt trên Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 3. Cài đặt trên macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Cấu trúc bản đồ Sokoban

| Ký hiệu | Ý nghĩa |
|---|---|
| `%` | Tường hoặc chướng ngại vật |
| `A` | Vị trí ban đầu của agent |
| `B` | Thùng |
| `D` | Đích |
| `C` | Thùng đang nằm trên đích |
| Khoảng trắng | Ô sàn |

## 5. Giải Sokoban bằng dòng lệnh

### UCS

```powershell
python solve.py --map maps/map_02_small.txt --algorithm ucs
```

### A*

```powershell
python solve.py --map maps/map_02_small.txt --algorithm astar
```

Kết quả gồm:

- Danh sách hành động North, East, West, South.
- Tổng chi phí.
- Số node mở rộng.
- Số node được sinh.
- Frontier lớn nhất.
- Thời gian chạy.

## 6. GUI một agent

```powershell
python run_gui.py --map maps/map_02_small.txt
```

Phím điều khiển:

| Phím | Chức năng |
|---|---|
| `U` | Chọn UCS |
| `A` | Chọn A* |
| `Space` | Chạy hoặc tạm dừng |
| `←` | Lùi một bước |
| `→` | Tiến một bước |
| `R` | Đặt lại |
| `Esc` | Thoát |

## 7. Benchmark UCS và A*

```powershell
python benchmark.py
```

Kết quả được lưu tại:

```text
results/benchmark.csv
```

Benchmark so sánh:

- Tổng chi phí.
- Thời gian.
- Peak memory.
- Số node mở rộng.
- Số node sinh.
- Frontier lớn nhất.

## 8. Kiểm chứng heuristic

```powershell
python heuristic_validation.py
```

Kết quả được lưu tại:

```text
results/heuristic_validation.csv
```

Chương trình kiểm tra:

- `h(goal) = 0`.
- Tính admissible.
- Tính consistent.

Heuristic sử dụng khoảng cách BFS có xét tường và phép ghép
một-một tối ưu giữa thùng và đích. Heuristic không sử dụng
khoảng cách Manhattan hoặc Euclidean.

## 9. Chế độ competitive trên terminal

```powershell
python run_competitive.py --map maps/map_competitive.txt --steps 20
```

- Agent 1 sử dụng BFS.
- Agent 2 sử dụng GBFS.
- Mỗi agent có tối đa 1000 ms để quyết định một hành động.

## 10. GUI competitive

```powershell
python run_competitive_gui.py --map maps/map_competitive.txt --steps 20
```

Phím điều khiển:

| Phím | Chức năng |
|---|---|
| `Space` | Chạy hoặc tạm dừng |
| `←` | Lùi một lượt |
| `→` | Tiến một lượt |
| `↑` | Tăng tốc |
| `↓` | Giảm tốc |
| `R` | Về trạng thái đầu |
| `Esc` | Thoát |

## 11. Luật giải quyết xung đột

Nếu hai agent cùng đi vào một vị trí hoặc cùng đẩy một thùng:

1. Sinh ngẫu nhiên `p` theo phân phối đều liên tục trên `[0, 1)`.
2. Nếu `p < 0.5`, Agent 1 hành động và Agent 2 mất lượt.
3. Nếu `p >= 0.5`, Agent 2 hành động và Agent 1 mất lượt.

Chạy demo:

```powershell
python demo_conflict_probability.py
```

## 12. Chạy kiểm thử

```powershell
python -m tests.test_map_loader
python -m tests.test_state
python -m tests.test_node
python -m tests.test_ucs
python -m tests.test_heuristic
python -m tests.test_astar
python -m tests.test_competitive_map_loader
python -m tests.test_competitive_state
python -m tests.test_game_engine
python -m tests.test_agent_1
python -m tests.test_agent_2
python -m tests.test_match_runner
```

## 13. Thuật toán competitive

Hai thuật toán điều khiển được đặt trong hai file riêng:

```text
competitive/agent_1.py
competitive/agent_2.py
```

Điều này cho phép thay thế agent để các nhóm thi đấu với nhau.