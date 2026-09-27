## 4.6. RQ3 – Detection Effectiveness vs Computational Overhead

RQ3 xem xét quan hệ giữa hiệu quả phát hiện, tỷ lệ báo động giả và chi phí tính toán của các bộ phát hiện. Bảng 4.y so sánh bộ phát hiện giao thức E1, đại diện cho baseline MB/MCM, với RF và SVM trên đặc trưng hành vi (E2) và với cấu hình lai (Hybrid, E3). Recall và FPR được tính trên tập kiểm tra và lấy trung bình qua năm hạt giống. Thời gian xử lý là thời gian dựng vectơ đặc trưng cho một phiên từ các bản ghi sự kiện, dùng đúng mã trích xuất đặc trưng của pipeline. Thời gian suy luận là thời gian đưa ra một quyết định cho một vectơ đặc trưng. Cả hai được đo bằng trung vị của 200 lần gọi đơn lẻ, trên máy chủ CPU 4 vCPU Intel Xeon 2.8 GHz, Python 3.11 và scikit-learn 1.9 [7].

Bảng 4.y. Hiệu quả phát hiện và chi phí tính toán theo phiên

| Phương pháp | Recall | FPR | Thời gian xử lý (ms/phiên) | Thời gian suy luận (ms/quyết định) | Cấu trúc mô hình |
|---|---|---|---|---|---|
| MB/MCM (E1, ngưỡng giao thức) | 1.000 | 0.000 | 6.07 | 0.17 | 1 đặc trưng, 1 ngưỡng |
| RF (E2) | 1.000 | 0.000 | < 0.001 | 23.04 (0.49) | 300 cây, 900 nút |
| SVM (E2) | 1.000 | 0.000 | < 0.001 | 1.48 (0.03) | 9 vectơ hỗ trợ |
| Hybrid – RF (E3) | 1.000 | 0.000 | 6.07 | 23.05 (0.47) | 300 cây, 902 nút |
| Hybrid – SVM (E3) | 1.000 | 0.000 | 6.07 | 1.56 (0.03) | 11 vectơ hỗ trợ |

Recall và FPR có độ lệch chuẩn bằng 0 trên năm hạt giống; kết quả không đổi khi gom nhóm theo thẻ vật lý. Giá trị trong ngoặc là thời gian trung bình mỗi mẫu khi dự đoán theo lô trên tập kiểm tra.

Do mọi phương pháp đều đạt Recall 1.000 và FPR 0.000, trục hiệu quả và trục báo động giả không phân biệt được các phương pháp, và sự đánh đổi của RQ3 chỉ còn thể hiện trên trục chi phí. Chi phí của bằng chứng giao thức nằm chủ yếu ở khâu trích xuất đặc trưng: tính 13 thống kê va chạm cho một phiên mất 6.07 ms khi gọi đơn lẻ (1.04 ms/phiên khi xử lý theo lô), chưa kể 1.39 ms/phiên để ghép cặp các lượt đọc chéo từ sự kiện thô. Đặc trưng hành vi `read_count` chỉ là một phép đếm, tốn dưới 1 µs. Ở khâu suy luận, ngưỡng E1 mất 0.17 ms, SVM mất khoảng 1.5 ms, còn RF mất khoảng 23 ms. Khoảng cách của RF chủ yếu do chi phí gọi tuần tự 300 cây trong scikit-learn, vì khi dự đoán theo lô thời gian mỗi mẫu chỉ còn 0.49 ms. Cấu hình Hybrid cộng dồn chi phí của cả hai khâu, tổng cộng khoảng 29 ms/phiên với RF và 7.6 ms/phiên với SVM, nhưng không cải thiện Recall hay FPR so với E2. Cấu trúc mô hình cũng cho thấy bài toán không đòi hỏi độ phức tạp này: mỗi cây trong rừng chỉ có ba nút, tức một phép so sánh ngưỡng duy nhất, nên 300 cây là dư thừa, và SVM chỉ cần 9–11 vectơ hỗ trợ. Kết quả này nhất quán với nhận định ở mục 4.5 rằng hai lớp tách được bằng một ngưỡng trên nhiều đặc trưng khác nhau.

Hai giới hạn quyết định cách diễn giải Bảng 4.y. Thứ nhất, các giá trị Recall và FPR không thể xem là hiệu quả an ninh: mục 4.5 cho thấy đặc trưng mà E1 sử dụng (`negative_dt_ratio`) chỉ còn AUC 0.546 khi hai lớp được xử lý đồng nhất. Vì vậy, Bảng 4.y không cho phép kết luận rằng baseline giao thức đạt cùng mức an ninh với chi phí thấp nhất; phần có giá trị của bảng là các số đo chi phí, vốn không phụ thuộc vào tính hợp lệ của nhãn. Thứ hai, độ trễ ra quyết định trong triển khai bị chi phối bởi thời gian quan sát hơn là thời gian tính toán. Các bộ phát hiện hoạt động ở mức phiên, nên chỉ đưa ra quyết định sau khi phiên kết thúc. Trung vị độ dài phiên là 219 giây ở S1, 37 giây ở S2 và 6 giây ở S3, cao hơn chi phí tính toán từ khoảng hai đến sáu bậc độ lớn. Hơn nữa, các phép đo được thực hiện trên CPU máy chủ, không phải trên ESP32 hay phần cứng tại điểm kiểm soát. Kích thước của các mô hình (tối đa 902 nút cây hoặc 11 vectơ hỗ trợ) là nhỏ so với bộ nhớ SRAM 520 KB của ESP32 [8], nhưng chưa có phép đo nào trên thiết bị nhúng. Do đó, kết quả chỉ hỗ trợ nhận định về tính khả thi tính toán cho triển khai định hướng điểm kiểm soát (computational feasibility for checkpoint-oriented deployment), không hỗ trợ tuyên bố về khả năng phát hiện thời gian thực.

### References (tiếp nối mục 4.5)

[7] F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, and É. Duchesnay, "Scikit-learn: Machine learning in Python," *Journal of Machine Learning Research*, vol. 12, pp. 2825–2830, 2011.

[8] Espressif Systems, *ESP32 Series Datasheet*, Espressif Systems, Shanghai, China.

---

Tái lập số liệu: `export RFID_DATA=...; cd ../analysis_4_5 && python rq3_cost_benchmark.py`
