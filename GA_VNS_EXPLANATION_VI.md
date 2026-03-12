# Phân Tích Cơ Chế Lập Lịch GA-VNS và Ứng Dụng Thực Tiễn

Chào bạn, đây là tài liệu giải thích cách hệ thống GA-VNS hoạt động để tối ưu hóa việc phân chia công việc cho các máy cắt, kèm theo ví dụ trực quan về vai trò của "Độ phức tạp" (Complexity).

## 1. Cơ Chế Hoạt Động Của GA-VNS

**Đề bài:** Bạn có 10 tấm vật liệu cần cắt (10 Jobs) và 3 máy cắt CNC. Máy 1 chuyên cắt nhanh nhưng chỉ cắt thẳng tốt (ví dụ Cắt cầu). Máy 2 và 3 xịn hơn (Waterjet/Lasers) cắt được đường cong phức tạp nhưng tốc độ có thể chậm hơn hoặc chi phí vận hành cao hơn. Làm sao để chia 10 tấm này cho 3 máy sao cho lúc hoàn thành xong là **sớm nhất**?

### Bước 1: GA (Genetic Algorithm - Thuật Toán Di Truyền) - Tạo Ra Nhiều Kịch Bản Phân Công Ngẫu Nhiên
Giống như quá trình tiến hóa, hệ thống sẽ tự động sinh ra khoảng 50 "Kịch bản" (Nhiễm sắc thể) khác nhau.
- **Kịch bản A:** Cho Máy 1 chạy Job 1, 2, 3; Máy 2 chạy Job 4, 5...
- **Kịch bản B:** Cho Máy 3 chạy Job 1, 2, 3; Máy 1 chạy Job 4, 5...

Thuật toán sẽ đánh giá độ tốt (Fitness) của từng kịch bản này dựa trên:
1. **Makespan**: Thời gian máy cuối cùng làm xong là bao lâu? (Càng ngắn càng tốt).
2. **Setup Time**: Thời gian dư thừa khi máy phải đợi gá đặt hoặc thay đổi phôi.
3. **Tardiness**: Có đơn hàng nào bị trễ `Due Date` (Hạn chót) không?

Sau đó, nó sẽ chọn ra những kịch bản tốt nhất để "Lai tạo" (Crossover) chéo với nhau, sinh ra các kịch bản lai ưu việt hơn thế hệ trước.

### Bước 2: VNS (Variable Neighborhood Search - Tìm Kiếm Cục Bộ) - Sửa Lỗi Tinh Chỉnh Nhanh
Đôi khi, GA lai tạo ra một kịch bản rất tốt (giả sử hoàn thành mất 120 phút), nhưng chỉ vì 2 công việc bị xếp ngược thứ tự do xui xẻo nên bị kẹt.
Lúc này, VNS nhảy vào làm nhiệm vụ "Dọn dẹp vi mô". Nó sẽ thử lấy kịch bản tốt đó và tạo ra các biến thể nhỏ:
- **N1 (Swap)**: Đổi chỗ thử Job 2 và Job 4 xem có nhanh hơn không?
- **N2 (Insert)**: Rút thử Job 5 chèn lên đầu tiên có tốt hơn không?

Nếu sự thay đổi nhỏ lẻ này giúp giảm thời gian xuống còn 110 phút, nó sẽ ghi nhận kịch bản này làm kết quả mới.

**Tóm lại:** GA dùng mẻ lưới khổng lồ để bắt bầy cá lớn (Tìm hướng tiếp cận tốt nhất trên toàn cục), sau đó VNS dùng vợt nhỏ để vớt từng con cá còn sót (Tinh chỉnh từng chi tiết nhỏ để ra kết quả hoàn hảo).

---

## 2. "Độ Phức Tạp" (Complexity) Dùng Để Làm Gì?

Trong hàm `dxf_parser.py`, độ phức tạp được tính bằng công thức:
`Complexity = Chiều dài đường cong / (Tổng chiều dài đường cong + đường thẳng)`

**Tại sao lại cần chỉ số này?**
Nó dùng để ra quyết định **Chọn lựa máy móc hợp lý (Constraint)** trong thuật toán lai tạo GA:

*Ví dụ Trực Quan:*
- **File DXF 1 (Tủ bếp vuông vắn - Complexity = 0.05)**:
  Có tổng chiều dài đường cắt là `10,000 mm`. Trong đó toàn bộ là đường thẳng (LINE). Đường cong (ARC) bằng 0.
  => Hệ thống AI/Hybrid Engine đọc thấy `Complexity < 0.1` (Cực kỳ đơn giản). Thuật toán lập lịch GA-VNS lập tức được phép phân công ném file này cho máy "Cắt Cầu" (chuyên cắt đường thẳng tốc độ cao).

- **File DXF 2 (Hoa văn trống đồng trang trí - Complexity = 0.85)**:
  Có tổng chiều dài đường cắt là `10,000 mm`. Nhưng nó có vô số đường cong lượn sóng chạm khắc, khiến `curved_len_mm = 8,500 mm`.
  => Hệ thống AI/Hybrid Engine đọc thấy `Complexity > 0.3`. Nếu ném file này cho máy "Cắt Cầu", mũi dao có thể bị gãy, hoặc sản phẩm bị phế. Hệ thống kích hoạt **"Ràng Buộc Chuyên Gia"**. Thuật toán GA-VNS lúc này bị ép: **Tuyệt đối không được giao Job này cho Máy Cắt Cầu**, mà chỉ được phép tìm thời gian rảnh trên Máy Tia Nước (Waterjet) hoặc CNC router tỉ mỉ.

**Kết luận:** Điểm `Complexity` chính là "bộ lọc năng lực", giúp thiết lập rào cản ngăn không cho thuật toán GA giao việc mù quáng cho một cái máy không có đủ trình độ để cắt bản vẽ đó!

---

## 3. Các Giải Pháp Xử Lý Các Vấn Đề (Sẽ Cập Nhật Tại Phiên Bản Này)

1. **Vấn đề 1: Chọn nhiều file cắt tối ưu -> Sửa phần DXF**
   - *Cách sửa:* Bật tính năng `accept_multiple_files=True` ở nút Upload của Streamlit `main.py`.
   - *Logic:* Sửa lại để vòng lặp chạy qua toàn bộ danh sách các file DXF được tải lên, cộng dồn tổng chiều dài `total_len_mm` và tính trung bình độ phức tạp, gộp chung thành một `Job` tổng chứa các cụm bản vẽ đó (hoặc chia làm nhiều Job nếu bạn cần).

2. **Vấn đề 2: Bổ sung "Due date" và "Mức độ ưu tiên" -> Giao diện**
   - *Cách sửa:* Thêm 1 trường Ngày tháng (hoặc Giờ dự kiến giao) và 1 hộp dropdown "Độ ưu tiên: Bình thường/Cao/Rất Cao" trong phần nhập đơn.
   - *Tương tác:* Nếu chọn "Rất Cao", tham số này sẽ truyền vào GA-VNS, kích hoạt hệ thống ghim chặt Job này vào vị trí đầu tiên hoặc đánh dấu trọng số cực nặng vào hàm Fitness `Tardiness` (để thuật toán sợ, phải đẩy lên đầu).

3. **Vấn đề 3: Sắp xếp lại quy trình gia công**
   - *Cách sửa:* Tôi sẽ cấu hình lại danh sách lựa chọn quy trình trong `main.py` để phù hợp hơn với thực tế vận hành.
