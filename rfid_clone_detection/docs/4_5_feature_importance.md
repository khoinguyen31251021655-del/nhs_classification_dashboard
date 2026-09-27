## 4.5. Feature Importance and Security Interpretation

Do cả ba cấu hình E1, E2, E3 và hai bộ phân loại đều đạt 1.000 ở mọi chỉ số (mục 4.3), phép so sánh ablation không lượng hóa được đóng góp của từng nguồn bằng chứng. Chúng tôi vì vậy phân tích quy kết đặc trưng để xác định mô hình dựa vào bằng chứng an ninh hay vào lối tắt phát sinh từ dữ liệu (shortcut learning) [1]. Mô hình RF của E3 được phân tích bằng ba thước đo trên năm hạt giống: độ quan trọng Gini, vốn thiên lệch khi các đặc trưng tương quan [2]; độ quan trọng hoán vị trên tập kiểm tra [3]; và giá trị SHAP ước lượng bằng TreeExplainer [4]. Kết quả quy kết được đối chiếu với nguồn gốc của từng đặc trưng và với một phân tích độ nhạy, trong đó đặc trưng giao thức của S2 và S3 được dẫn xuất lại từ sự kiện đọc thô theo cùng một quy tắc: cùng quy ước dấu Δ = t_B − t_A, cùng lưới thời gian 1 ms, cùng cửa sổ đồng hiện diện w = 5 ms, và chuẩn hóa theo xác suất trùng hợp ngẫu nhiên p₀ = 1 − exp(−2wλ_B) của hai reader đọc độc lập với tốc độ λ_B.

Độ quan trọng phân bố gần như đều trên 11 đặc trưng (Gini từ 0.077 đến 0.097), thứ hạng dao động mạnh giữa các hạt giống (chẳng hạn `dt_std` xếp từ thứ nhất đến thứ mười một), và độ quan trọng hoán vị bằng 0 với cả 14 đặc trưng. Nguyên nhân là 11 trong 14 đặc trưng tự phân tách hoàn toàn hai lớp (AUC đơn biến bằng 1.000): khi nhiều đặc trưng dư thừa cùng đủ để phân loại, mô hình chọn giữa chúng một cách ngẫu nhiên và nhiễu ở một đặc trưng được các đặc trưng còn lại bù đắp. Thứ hạng quy kết do đó không đủ để xác định bằng chứng mà mô hình sử dụng; điều cần xem xét là nguồn gốc của khả năng phân tách (Bảng 4.x).

Bảng 4.x. Nguồn gốc khả năng phân tách của các đặc trưng E3 và kết quả sau khi dẫn xuất đồng nhất

| Cơ chế | Đặc trưng E3 chịu ảnh hưởng | Tỷ trọng \|SHAP\| | Chỉ số sau dẫn xuất đồng nhất (thật / nhân bản) | AUC trước → sau |
|---|---|---|---|---|
| Quy ước dấu (S2 lưu Δ có dấu, S3 lưu \|Δ\|) | `negative_dt_ratio`, `positive_dt_ratio`, `dt_min`, `dt_mean`, `dt_median` | 26.6% | Tỷ lệ Δ âm: 0.458 / 0.433 | 1.000 → 0.546 |
| Cửa sổ ghép cặp (S3 ≤ 5 ms, S2 ≤ 760 ms) | `dt_std`, `dt_max`, `dt_abs_mean`, `dt_abs_median`, `small_dt_*_ratio`, `collision_count` | 64.5% | Đồng hiện diện so với p₀: 2.69 / 2.01 | 1.000 → 0.834ᵃ |
| Định nghĩa `read_count` khác nhau giữa hai lớp | `read_count` | 8.7% | Lượt đọc mỗi reader: 147.25 / 150.00 | 1.000 → 1.000ᵇ |
| Độ phân giải thời gian (S3 trên lưới mili-giây) | `zero_dt_ratio` | 0.1% | Tỷ lệ Δ = 0: 0.083 / 0.107 | 0.944 → 0.602 |

ᵃ Giá trị cao hơn ở lớp thật. ᵇ Lớp nhân bản không có lượt đọc hụt.

Toàn bộ tỷ trọng SHAP rơi vào các đặc trưng chịu ảnh hưởng của những khác biệt trong cách tóm tắt dữ liệu hai lớp. Tệp S3 lưu |t_B − t_A| trong khi tệp S2 lưu hiệu có dấu, nên `negative_dt_ratio`, cũng là đặc trưng mà bộ phát hiện E1 lựa chọn, bằng 0 ở lớp nhân bản; khi tính lại hiệu có dấu từ các mốc thời gian của S3, tỷ lệ giá trị âm là 44.7%, tương đương S2. Tệp S3 chỉ giữ các cặp đọc có |Δ| ≤ 5 ms, trong khi S2 ghép cặp đến 760 ms, còn `read_count` là tổng lượt đọc theo kế hoạch thí nghiệm (100 hoặc 150) ở lớp thật nhưng là số cặp đọc trùng (50–83) ở lớp nhân bản. Sau khi dẫn xuất đồng nhất, tần suất đồng hiện diện thô vẫn cao hơn ở lớp nhân bản (0.447 so với 0.103), song tốc độ đọc của S3 cao gấp 6.4 lần S2 (50.3 so với 7.9 Hz), và khi chuẩn hóa theo p₀ thì lớp thật lại đồng bộ vượt mức ngẫu nhiên nhiều hơn (2.69 so với 2.01 lần). Các đặc trưng còn tách hoàn toàn hai lớp chỉ gồm tốc độ đọc, thời lượng phiên và mức đầy đủ của luồng đọc. Điều này phù hợp với việc toàn bộ 108 phiên S3 nằm trong khoảng 6 giây, mỗi phiên đúng 300 sự kiện, tức lớp nhân bản nhiều khả năng được sinh bằng phần mềm như tài liệu bộ dữ liệu đã đề cập [5]. Khi ánh xạ lại các phiên S3 về 12 thẻ vật lý, thay cho 108 nhóm phát sinh do không trích được tên thẻ từ `session_id`, RF và SVM vẫn đạt 1.000 trên cả năm hạt giống. Kết quả vì thế không đến từ việc ghi nhớ danh tính thẻ mà từ rò rỉ trong quá trình xây dựng dữ liệu [6].

Đối với câu hỏi detector dựa vào bằng chứng an ninh nào, kết quả cho thấy trên RFID-ExSim các bộ phát hiện chưa sử dụng những bằng chứng được giả thuyết ở mục 3.3. Tín hiệu nhiều reader cùng đọc một UID xuất hiện ở cả hai lớp, vì một thẻ thật nằm trong vùng phủ chồng lấn của S2 cũng được hai reader đọc gần như đồng thời; khoảng cách thời gian giữa hai reader chỉ đúng chiều kỳ vọng trước khi chuẩn hóa theo tốc độ đọc; còn chuyển tiếp reader bất khả thi không xác định được do bộ dữ liệu không có thông tin vị trí reader. Sự đồng hiện diện của một UID chỉ trở thành bằng chứng nhân bản khi gắn với một ràng buộc không gian, nghĩa là bằng chứng nhân bản mang tính quan hệ giữa danh tính, bố trí reader và thời gian, chứ không phải thống kê của từng phiên đọc. Từ đó, hiệu năng 1.000 ở mục 4.2–4.3 chưa thể xem là bằng chứng ủng hộ RQ1. RQ2 cũng chưa được kiểm định, vì ngoài hiện tượng bão hòa, mỗi mẫu lớp thật của E3 ghép đặc trưng giao thức của một phiên S2 với `read_count` của một phiên S1. Về mặt an ninh, một đối thủ đã sao chép được UID có thể né bộ phát hiện hiện tại bằng cách tạo luồng đọc có nhịp giống thẻ thật. Các yêu cầu cho thiết kế đánh giá tiếp theo, gồm dẫn xuất đặc trưng hai lớp qua cùng một quy trình, biểu diễn bằng chứng giao thức ở dạng chuẩn hóa theo tốc độ đọc, bổ sung thông tin bố trí reader và thu lớp nhân bản trên phần cứng, được trình bày ở mục 5.3–5.4.

### References

[1] R. Geirhos, J.-H. Jacobsen, C. Michaelis, R. Zemel, W. Brendel, M. Bethge, and F. A. Wichmann, "Shortcut learning in deep neural networks," *Nature Machine Intelligence*, vol. 2, no. 11, pp. 665–673, 2020.

[2] C. Strobl, A.-L. Boulesteix, A. Zeileis, and T. Hothorn, "Bias in random forest variable importance measures: Illustrations, sources and a solution," *BMC Bioinformatics*, vol. 8, Art. no. 25, 2007.

[3] G. Hooker, L. Mentch, and S. Zhou, "Unrestricted permutation forces extrapolation: Variable importance requires at least one more model, or there is no free variable importance," *Statistics and Computing*, vol. 31, no. 6, Art. no. 82, 2021.

[4] S. M. Lundberg, G. Erion, H. Chen, A. DeGrave, J. M. Prutkin, B. Nair, R. Katz, J. Himmelfarb, N. Bansal, and S.-I. Lee, "From local explanations to global understanding with explainable AI for trees," *Nature Machine Intelligence*, vol. 2, no. 1, pp. 56–67, 2020.

[5] RFID-ExSim Dataset, "Experiment Scenarios (S1–S5)," dataset documentation, `docs/scenarios.md`.

[6] S. Kaufman, S. Rosset, C. Perlich, and O. Stitelman, "Leakage in data mining: Formulation, detection, and avoidance," *ACM Transactions on Knowledge Discovery from Data*, vol. 6, no. 4, Art. no. 15, 2012.

---

Bản đầy đủ (4 bảng, dùng cho phụ lục hoặc trả lời phản biện): `4_5_feature_importance_full.md`. Script tái lập số liệu: `../analysis_4_5/`.
