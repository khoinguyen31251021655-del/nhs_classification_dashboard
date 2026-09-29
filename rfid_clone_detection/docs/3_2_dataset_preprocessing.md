## 3.2. RFID-ExSim Dataset and Preprocessing

Nghiên cứu sử dụng bộ dữ liệu RFID-ExSim [5], thu bằng hai reader ESP32-MFRC522 và 12 thẻ RFID thụ động trong năm kịch bản S1–S5. Mỗi sự kiện đọc là một bản ghi JSON gồm mốc thời gian UTC (độ phân giải micro-giây), mã phiên, reader, nhãn thẻ, UID, khoảng cách, góc đặt thẻ và loại sự kiện. Trong 408 422 sự kiện của bộ dữ liệu, 331 242 sự kiện thuộc S4 (replay) và S5 (flooding), nằm ngoài phạm vi nghiên cứu. Phân tích chỉ dùng 77 180 sự kiện của ba kịch bản: S1 (đọc cơ sở theo lưới khoảng cách 1, 3, 4 cm và góc 0°, 45°, 90°), S2 (hai reader cùng đọc hợp lệ một thẻ trong vùng phủ chồng lấn) và S3 (cùng một UID xuất hiện đồng thời ở hai reader). S1 và S2 được gán nhãn thật, S3 được gán nhãn nhân bản; S2 được đưa vào vì đây là nguồn duy nhất cho phép quan sát bằng chứng va chạm hai reader ở lớp thật.

Bảng 3.x. Kết quả kiểm tra dữ liệu ở mức sự kiện

| | S1 (thật) | S2 (thật) | S3 (nhân bản) |
|---|---|---|---|
| Sự kiện / lượt đọc thành công | 13 004 / 12 472 | 31 776 / 31 776 | 32 400 / 32 400 |
| Phiên | 108 | 108 | 108 |
| Reader / thẻ / UID | 2 / 12 / 12 | 2 / 12 / 12ᵃ | 2 / 12 / 12 |
| Khoảng thời gian (UTC, 2025) | 04/11 – 09/11 | 10/11, 13:03 – 13:08 | 11/11, 10:38:05 – 10:38:12 |
| Trung vị độ dài phiên | 219 s | 37 s | 6 s |
| Bản ghi trùng lặp / thiếu giá trị | 0 / 532ᵇ | 0 / 0 | 0 / 0 |

ᵃ Khác với UID của cùng nhãn thẻ ở S1 và S3. ᵇ Thông điệp khởi động của firmware, không có nhãn thẻ và UID.

Ba kịch bản không có bản ghi trùng lặp (Bảng 3.x). Giá trị thiếu chỉ xuất hiện ở 532 dòng của S1 (4.1%); đây là thông điệp khởi động của firmware ESP32 bị ghi lẫn vào nhật ký và được loại bỏ. Vì trường `total_reads` trong tệp tóm tắt của S1 tính cả những dòng này (73/108 phiên bị ảnh hưởng), số lượt đọc của S1 được lấy từ `success_reads`. UID của S2 không khớp với UID của cùng nhãn thẻ ở S1 và S3, và trường `uid_hash` được tạo theo ba cách khác nhau giữa các kịch bản. Do đó `tag_local_id` được dùng làm khóa nhóm, còn mọi trường định danh đều bị loại khỏi tập đặc trưng. Tỷ lệ thật : nhân bản là 1.37:1 ở mức lượt đọc (44 248 so với 32 400) và 2:1 ở mức phiên (216 so với 108), rồi trở về 1:1 sau khi dựng mẫu, nên không cần lấy mẫu lại.

Đơn vị phân tích là phiên đọc (`session_id`), tức một lần trình diện một thẻ tại một tổ hợp khoảng cách × góc × lượt chạy; cửa sổ tổng hợp là toàn bộ phiên, không dùng cửa sổ trượt. Với mỗi phiên, bằng chứng giao thức gồm 13 thống kê trên hiệu thời gian Δ giữa hai reader, tính từ các bản ghi va chạm và quy về đơn vị giây: số bản ghi; trung bình, độ lệch chuẩn, trung vị, cực tiểu và cực đại của Δ; trung bình và trung vị của |Δ|; tỷ lệ |Δ| ≤ 10 ms và ≤ 50 ms; tỷ lệ Δ dương, âm và bằng 0. Bằng chứng hành vi là số lượt đọc của phiên, gồm số lượt đọc thành công ở S1 và số bản ghi va chạm ở S3. Mẫu nhân bản lấy cả hai loại bằng chứng từ cùng một phiên S3. Mẫu thật ghép bằng chứng giao thức của một phiên S2 với bằng chứng hành vi của phiên S1 có cùng nhãn thẻ và cùng thứ tự trong thẻ. Kết quả là 216 mẫu mức phiên (108 mẫu mỗi lớp) với 14 đặc trưng. Mỗi mẫu mang nhãn thẻ vật lý làm khóa nhóm để chia dữ liệu ở mục 3.5; với S3, nhãn thẻ được lấy từ kế hoạch thí nghiệm `s3_plan.csv`.

---

Tái lập số liệu: `export RFID_DATA=...; python ../analysis_4_5/audit_3_2.py`. Trích dẫn [5] là tài liệu mô tả bộ dữ liệu, giống [5] ở mục 4.5.
