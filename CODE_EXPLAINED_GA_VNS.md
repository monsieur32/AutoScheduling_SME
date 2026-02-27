# Giải Thích Chi Tiết Thuật Toán GA-VNS (ga_vns.py)

Tài liệu này giải thích chi tiết chức năng của từng hàm trong module `ga_vns.py`, được phát triển dựa trên thuật toán Genetic Algorithm với Variable Neighborhood Search (GA-VNS) cho bài toán Lập lịch phân xưởng linh hoạt (FJSP) được đề cập trong tài liệu nghiên cứu.

## 1. Class `GAVNSSolver`
Đây là lớp chính thực hiện toàn bộ quá trình tối ưu hóa.

### `__init__(self, jobs, machines_data, ...)`
- **Chức năng**: Khởi tạo bộ giải.
- **Hoạt động**:
  - Nhận vào danh sách công việc (`jobs`), dữ liệu máy móc, hàm tính thời gian.
  - Lọc ra các máy phù hợp cho mỗi công việc dựa trên độ phức tạp (`capabilities` như `Cut_contour` hay `Cut_straight`).
  - Xây dựng ma trận `processing_times` chứa thời gian thực thi của mỗi phép toán trên từng máy hợp lệ.
  - Tính toán **Total Work Content (TWK)** là tổng thời gian lý tưởng ngắn nhất để hoàn thành một công việc.
  - Tính toán **Due Date (Thời hạn)** bằng cách nhân TWK với `tightness_factor`.

### `get_setup_time(self, m_id, prev_job_id, curr_job_id)`
- **Chức năng**: Lấy thời gian gá đặt phụ thuộc chuỗi (Sequence-Dependent Setup Time).
- **Hoạt động**: Trích xuất `setup_matrix` từ cấu hình của máy. Nếu là công việc đầu tiên hoặc cùng một công việc chạy tiếp, setup time = 0. Nếu không có dữ liệu, trả về mặc định `5` phút.

## 2. Các Chiến Lược Khởi Tạo Quần Thể (Multi-Strategy Initialization)
Thuật toán chia quần thể ban đầu làm 4 nhóm bằng nhau (mỗi nhóm 25%) để tạo sự đa dạng và chất lượng nghiệm ban đầu.
- **`random_machine_selection(self)`**: Chọn máy ngẫu nhiên cho mỗi phép toán (Machine Selection - MS).
- **`spt_machine_selection(self)`**: Chọn máy có Thời gian thực thi ngắn nhất (Shortest Processing Time). Giúp hội tụ nhanh hơn.
- **`random_operation_sequence(self)`**: Sắp xếp ngẫu nhiên thứ tự thực thi của các phép toán (Operation Sequence - OS).
- **`lwkr_fdd_operation_sequence(self)`**: Sắp xếp dựa theo Least Work Remaining và Flow Due Date. Ở đây được diễn dịch bằng cách ưu tiên các Job có chênh lệch `(Due Date - TWK)` thấp nhất.
- **`cr_operation_sequence(self)`**: Dựa trên Critical Ratio (Tỷ lệ tới hạn). Ưu tiên các Job có tỷ lệ `Due Date / Cấp bách` thấp.
- **`initialize_population(self)`**: Kết hợp 4 chiến lược tạo ra các cá thể MS và OS như P1 (Random MS, Random OS), P2, P3, P4 trong bài báo.

## 3. Hàm Đánh Giá Fitness
### `decode_and_evaluate(self, individual)`
- **Chức năng**: Giải mã chuỗi gen (MS và OS) thành 1 lịch trình thực tế và trả về điểm Fitness.
- **Hoạt động**:
  - Quét qua mảng OS. Lấy máy tương ứng ở mảng MS.
  - Thiết lập thời gian Bắt đầu = `max(Máy rảnh lúc, Job rảnh lúc)`.
  - Tính toán Setup Time nếu cần chuyển đổi Job trên cùng 1 máy.
  - Cập nhật thời gian hoàn thành (Finish Time) của Máy và Job.
  - Ghi nhận `Makespan` (Thời gian hoàn thành trễ nhất), `Total Setup Time` (Tổng thời gian thay lắp) và `Total Tardiness` (Tổng độ trễ hạn so với Due Date tính toán ban đầu).
  - Trả về độ thích nghi Fitness = `(Makespan + Total Setup Time + Total Tardiness) / 3`.

## 4. Các Toán Tử Di Truyền (GA Operators)
### `crossover_os(self, os1, os2)`
- Thực hiện lai ghép chuỗi nguyên công (Operation Sequence Crossover). Sử dụng cơ chế lai POX (Precedence Preserving Order-Based Crossover) để đảm bảo bảo toàn tính hợp lệ của số lượng nguyên công thuộc từng Job mà không gây lỗi.
### `crossover_ms(self, ms1, ms2)`
- Điểm lai đồng nhất cho MS: Mỗi gen Máy cho từng nguyên công có 50% cơ hội lấy từ Cha hoặc Mẹ.

## 5. Tìm Kiếm Cục Bộ VNS (VNS Local Search)
### `vns_local_search(self, individual)`
- **Chức năng**: Tránh việc GA bị mắc kẹt ở cực trị địa phương (Local Optima).
- **Hoạt động**: Áp dụng lần lượt 4 cấu trúc lân cận N1-N4 lên nhiễm sắc thể OS:
  - **N1 (Swap)**: Tráo đổi vị trí 2 phép toán bất kỳ.
  - **N2 (Reversion)**: Đảo ngược đoạn con của chuỗi nguyên công.
  - **N3 (Insertion)**: Rút 1 phép toán và chèn vào vị trí ngẫu nhiên khác.
  - **N4 (Rearrangement)**: Trộn ngẫu nhiên (Shuffle) 4 vị trí bất kỳ trong chuỗi.
- Trả về cá thể tốt hơn nếu sau khi thử nghiệm phát hiện cấu trúc OS mới cung cấp Fitness thấp hơn.

## 6. Vòng Lặp Giải Chính (The Main Loop)
### `solve(self)`
- Khởi tạo quần thể ban đầu.
- Trải qua `max_gen` số thế hệ. Ở mỗi thế hệ:
  - Lai ghép các lựa chọn tốt nhất (Top 50%).
  - Vận dụng Đột biến (Mutation 10%) và VNS Local Search (10%) lên các cá thể con.
  - Chọn lọc ra thế hệ kế tiếp. Ở đây áp dụng Elitism giữ lại 2 cá thể tốt nhất tuyệt đối không bị lai ghép thay đổi.
- Kết thúc: Trả về một hàm lịch trình chi tiết tốt nhất (`best_schedule`) tương thích với Streamlit UI ở frontend.
