## 3.2. RFID-ExSim Dataset and Preprocessing

Nghiên cứu sử dụng bộ dữ liệu RFID-ExSim [5], được thu bằng hai reader ESP32-MFRC522 (ESP32_A và ESP32_B) và 12 thẻ RFID thụ động (TAG01–TAG12) trong năm kịch bản S1–S5. Mỗi sự kiện đọc được lưu thành một bản ghi JSON với 11 trường chuẩn: mốc thời gian ISO-8601 (UTC, độ phân giải micro-giây), mã phiên, kịch bản, reader, nhãn thẻ, UID gốc, UID đã băm, khoảng cách, góc đặt thẻ, loại sự kiện và payload thô. Các tệp nhật ký hợp nhất chứa tổng cộng 408 422 sự kiện, trong đó 331 242 sự kiện thuộc S4 (replay) và S5 (flooding), nằm ngoài phạm vi phát hiện nhân bản UID của nghiên cứu. Phân tích vì vậy chỉ sử dụng 77 180 sự kiện của ba kịch bản. S1 gồm các lượt đọc cơ sở theo lưới khoảng cách (1, 3, 4 cm) và góc (0°, 45°, 90°). S2 gồm các lượt đọc hợp lệ khi hai reader cùng đọc một thẻ trong vùng phủ chồng lấn. S3 là kịch bản nhân bản, trong đó cùng một UID xuất hiện đồng thời ở hai reader. S1 và S2 được gán nhãn thật, S3 được gán nhãn nhân bản. S2 được đưa vào vì bằng chứng giao thức, vốn dựa trên va chạm giữa hai reader, chỉ quan sát được ở lớp thật khi có dữ liệu hai reader đọc đồng thời.

Bảng 3.x. Kết quả kiểm tra dữ liệu ở mức sự kiện

| | S1 | S2 | S3 |
|---|---|---|---|
| Nhãn | Thật | Thật | Nhân bản |
| Sự kiện / lượt đọc thành công | 13 004 / 12 472 | 31 776 / 31 776 | 32 400 / 32 400 |
| Số phiên | 108 | 108 | 108 |
| Reader / thẻ / UID | 2 / 12 / 12 | 2 / 12 / 12ᵃ | 2 / 12 / 12 |
| Khoảng thời gian (UTC, 2025) | 04/11 08:12 – 09/11 14:44 | 10/11 13:03 – 13:08 | 11/11 10:38:05 – 10:38:12 |
| Trung vị độ dài phiên | 219 s | 37 s | 6 s |
| Bản ghi trùng lặp | 0 | 0 | 0 |
| Bản ghi thiếu giá trị | 532 (4.1%)ᵇ | 0 | 0 |

ᵃ UID của S2 khác với UID của cùng nhãn thẻ trong S1, S3 và trong tệp danh mục thẻ. ᵇ Thông điệp khởi động của firmware (event = raw), không có nhãn thẻ, UID, khoảng cách và góc.

Dữ liệu của ba kịch bản không có bản ghi trùng lặp, dù xét trùng trên toàn bộ trường hay trùng theo cặp reader–mốc thời gian trong cùng phiên (Bảng 3.x). Giá trị thiếu chỉ xuất hiện ở 532 dòng của S1 (4.1%); đây là các thông điệp khởi động của firmware ESP32 bị ghi lẫn vào nhật ký, và chúng được loại trước khi tổng hợp. Việc loại bỏ này ảnh hưởng trực tiếp đến đặc trưng hành vi. Trong tệp tóm tắt phiên của S1, trường `total_reads` bằng số lượt đọc thành công cộng số dòng khởi động ở cả 108 phiên, và 73 phiên có ít nhất một dòng như vậy. Số lượt đọc của S1 vì thế được lấy từ `success_reads` (91–151 lượt đọc thành công mỗi phiên) thay vì `total_reads`. Hai bất thường khác được ghi nhận nhưng không ảnh hưởng đến đặc trưng: một phiên S1 có các mốc thời gian trải dài 26.6 giờ, và UID của S2 không khớp với UID của cùng nhãn thẻ ở S1 và S3. Ngoài ra, trường `uid_hash` được tạo theo ba cách khác nhau giữa các kịch bản và ở S3 chỉ là UID gốc viết thường, nên không thể dùng làm khóa định danh nhất quán. Nhãn `tag_local_id` được dùng làm khóa nhóm thay thế, và mọi trường định danh (mã phiên, UID, UID đã băm, nhãn thẻ) đều bị loại khỏi tập đặc trưng để mô hình không học theo danh tính.

Tỷ lệ giữa hai lớp thay đổi theo mức tổng hợp. Ở mức sự kiện, có 44 248 lượt đọc thành công thuộc lớp thật và 32 400 thuộc lớp nhân bản (1.37:1). Ở mức bản ghi va chạm, S2 có 31 664 cặp trong khi S3 có 7 100 cặp (4.46:1); chênh lệch này chủ yếu do hai tệp tóm tắt dùng cửa sổ ghép cặp khác nhau (mục 4.5). Ở mức phiên, lớp thật có 216 phiên (S1 và S2) so với 108 phiên của lớp nhân bản. Sau khi dựng mẫu theo quy tắc dưới đây, tập dữ liệu cuối cùng cân bằng với 108 mẫu mỗi lớp, nên không cần lấy mẫu lại. Các bộ phân loại vẫn dùng trọng số lớp cân bằng để giữ ổn định khi phép chia theo nhóm làm lệch tỷ lệ lớp trong từng tập.

Quy tắc chuyển từ sự kiện thô sang mẫu được xác định như sau. Đơn vị phân tích là phiên đọc (`session_id`), tương ứng với một lần trình diện một thẻ tại một tổ hợp khoảng cách × góc × lượt chạy theo kế hoạch thí nghiệm: mỗi thẻ có 9 phiên trong S1 và S2, và S3 gồm 36 cặp nhân bản × 3 lượt chạy. Cửa sổ tổng hợp là toàn bộ phiên, không dùng cửa sổ trượt. Với mỗi phiên, bằng chứng giao thức gồm 13 thống kê trên hiệu thời gian Δ giữa hai reader, tính từ các bản ghi va chạm và quy về đơn vị giây: số bản ghi; trung bình, độ lệch chuẩn, trung vị, giá trị nhỏ nhất và lớn nhất của Δ; trung bình và trung vị của |Δ|; tỷ lệ |Δ| ≤ 10 ms và ≤ 50 ms; và tỷ lệ Δ dương, âm, bằng 0. Bằng chứng hành vi là số lượt đọc của phiên, lấy từ số lượt đọc thành công ở S1 và số bản ghi va chạm ở S3. Mỗi mẫu của lớp nhân bản lấy cả hai loại bằng chứng từ cùng một phiên S3. Mỗi mẫu của lớp thật ghép bằng chứng giao thức của một phiên S2 với bằng chứng hành vi của phiên S1 có cùng nhãn thẻ và cùng thứ tự trong thẻ, vì S2 là nguồn bằng chứng giao thức còn S1 là nguồn bằng chứng hành vi cơ sở của lớp thật. Mỗi mẫu được gắn nhãn thẻ vật lý làm khóa nhóm cho phép chia dữ liệu ở mục 3.5; với S3, nhãn thẻ được lấy từ kế hoạch thí nghiệm (`s3_plan.csv`). Kết quả là 216 mẫu mức phiên, mỗi mẫu có 14 đặc trưng.

---

Tái lập số liệu: `export RFID_DATA=...; python ../analysis_4_5/audit_3_2.py`. Trích dẫn [5] là tài liệu mô tả bộ dữ liệu, giống [5] ở mục 4.5.
