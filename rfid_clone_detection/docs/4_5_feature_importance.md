## 4.5. Feature Importance and Security Interpretation

Ở các mục 4.2 và 4.3, cả ba cấu hình bằng chứng (E1, E2, E3) cùng hai bộ phân loại Random Forest (RF) và SVM đều đạt giá trị 1.000 ở mọi chỉ số đánh giá trên tập kiểm tra độc lập. Khi tất cả các cấu hình cùng đạt ngưỡng trần, phép so sánh ablation không còn đủ độ phân giải để lượng hóa đóng góp riêng của từng nguồn bằng chứng; hiệu số E3 − E2 bằng 0 trong trường hợp này phản ánh sự bão hòa của phép đo hơn là sự vắng mặt của đóng góp. Mục này vì vậy sử dụng phân tích quy kết đặc trưng để xem xét một câu hỏi gắn trực tiếp với RQ1 và RQ2: mô hình dựa vào những thông tin nào khi xếp một định danh vào lớp nhân bản, và các thông tin đó mang ý nghĩa an ninh hay chỉ phản ánh đặc điểm của quá trình xây dựng dữ liệu, hiện tượng được Geirhos và cộng sự (2020) mô tả là học theo lối tắt (shortcut learning).

### 4.5.1. Phương pháp quy kết

Phân tích được thực hiện trên mô hình RF của cấu hình E3, gồm 13 đặc trưng giao thức và đặc trưng hành vi `read_count`, do đây là cấu hình duy nhất chứa đồng thời cả hai họ bằng chứng. Ba thước đo bổ sung cho nhau được sử dụng. Độ quan trọng dựa trên mức giảm tạp chất Gini (Breiman, 2001) được tính trực tiếp từ mô hình nhưng có xu hướng thiên lệch khi các đặc trưng tương quan với nhau (Strobl và cộng sự, 2007). Độ quan trọng hoán vị (permutation importance) được đo bằng mức giảm F1 trên tập kiểm tra khi xáo trộn từng đặc trưng; thước đo này phản ánh tác động trên dữ liệu chưa thấy, song dễ bị đánh giá thấp khi thông tin của một đặc trưng đã được mang bởi các đặc trưng khác (Hooker và cộng sự, 2021). Giá trị SHAP được ước lượng bằng TreeExplainer (Lundberg và Lee, 2017; Lundberg và cộng sự, 2020), cho phép xem xét cả độ lớn lẫn chiều tác động ở mức từng mẫu. Toàn bộ quy trình được lặp lại với năm hạt giống ngẫu nhiên (42, 7, 123, 2024 và 99), mỗi hạt giống ứng với một phép chia theo nhóm khác nhau, nhằm đánh giá độ ổn định của thứ hạng.

Bên cạnh ba thước đo trên, chúng tôi truy xuất nguồn gốc của từng đặc trưng, tức là xem xét cách đặc trưng đó được tính cho mỗi lớp từ các tệp dữ liệu gốc, đồng thời thực hiện một phân tích độ nhạy trong đó các đặc trưng giao thức được dẫn xuất lại từ sự kiện đọc thô của S2 và S3 theo cùng một quy tắc.

### 4.5.2. Kết quả quy kết

Bảng 4.x. Độ quan trọng đặc trưng của mô hình RF trong cấu hình E3 (trung bình ± độ lệch chuẩn trên năm hạt giống)

| Đặc trưng | Gini | \|SHAP\| trung bình | Khoảng thứ hạng SHAP | Mức giảm F1 khi hoán vị | AUC đơn biến |
|---|---|---|---|---|---|
| `dt_abs_mean` | 0.097 ± 0.013 | 0.048 ± 0.006 | 1–10 | 0.000 | 1.000 |
| `dt_max` | 0.096 ± 0.013 | 0.048 ± 0.006 | 1–9 | 0.000 | 1.000 |
| `positive_dt_ratio` | 0.095 ± 0.008 | 0.048 ± 0.004 | 2–8 | 0.000 | 1.000 |
| `small_dt_50ms_ratio` | 0.095 ± 0.008 | 0.048 ± 0.004 | 2–7 | 0.000 | 1.000 |
| `dt_abs_median` | 0.095 ± 0.007 | 0.047 ± 0.004 | 1–7 | 0.000 | 1.000 |
| `dt_std` | 0.094 ± 0.017 | 0.047 ± 0.009 | 1–11 | 0.000 | 1.000 |
| `collision_count` | 0.091 ± 0.013 | 0.046 ± 0.006 | 3–11 | 0.000 | 1.000 |
| `read_count` | 0.087 ± 0.017 | 0.044 ± 0.009 | 2–11 | 0.000 | 1.000 |
| `negative_dt_ratio` | 0.084 ± 0.006 | 0.042 ± 0.003 | 5–10 | 0.000 | 1.000 |
| `dt_min` | 0.081 ± 0.012 | 0.041 ± 0.006 | 3–10 | 0.000 | 1.000 |
| `small_dt_10ms_ratio` | 0.077 ± 0.009 | 0.039 ± 0.004 | 7–11 | 0.000 | 1.000 |
| `dt_median` | 0.004 ± 0.006 | 0.002 ± 0.003 | 12–14 | 0.000 | 0.973 |
| `dt_mean` | 0.001 ± 0.003 | 0.001 ± 0.001 | 12–14 | 0.000 | 0.910 |
| `zero_dt_ratio` | 0.001 ± 0.001 | 0.001 ± 0.001 | 12–14 | 0.000 | 0.944 |

Độ quan trọng phân bố tương đối đồng đều trên 11 đặc trưng đầu, với giá trị Gini nằm trong khoảng 0.077–0.097, và thứ hạng của từng đặc trưng thay đổi đáng kể giữa các lần chạy; `dt_std`, `collision_count` và `read_count` chẳng hạn có thể xếp thứ nhất hoặc thứ hai ở lần chạy này nhưng thứ mười một ở lần chạy khác. Mức giảm F1 khi hoán vị bằng 0 với cả 14 đặc trưng, dù mô hình phân loại đúng toàn bộ tập kiểm tra. Các hiện tượng này nhất quán với việc 11 trong 14 đặc trưng có khả năng tự phân tách hoàn toàn hai lớp: miền giá trị của lớp thật và lớp nhân bản không giao nhau, và AUC đơn biến tương ứng bằng 1.000. Khi có nhiều đặc trưng dư thừa mà mỗi đặc trưng đều đủ để phân loại, việc lựa chọn giữa chúng tại các nút của cây mang tính ngẫu nhiên, và nhiễu đưa vào một đặc trưng được bù đắp bởi các đặc trưng còn lại. Thứ hạng trong Bảng 4.x do đó cho biết tồn tại nhiều cách tương đương để tách hai lớp, nhưng không chỉ ra được nguồn bằng chứng mà mô hình thực sự phụ thuộc vào. Việc lý giải khả năng phân tách này đòi hỏi xem xét cách các đặc trưng được xây dựng.

### 4.5.3. Nguồn gốc của khả năng phân tách

Việc truy xuất nguồn gốc cho thấy khả năng phân tách xuất phát từ bốn khác biệt trong cách dữ liệu của hai lớp được tóm tắt (Bảng 4.y). Khác biệt đầu tiên nằm ở quy ước dấu: tệp tóm tắt của S2 lưu hiệu thời gian có dấu Δ = t_B − t_A, trong khi tệp của S3 lưu giá trị tuyệt đối |t_B − t_A|. Hệ quả là tỷ lệ Δ âm xấp xỉ 0.50 ở lớp thật và bằng 0 ở lớp nhân bản. Khi hiệu có dấu được tính lại từ chính các mốc thời gian trong tệp S3, tỷ lệ giá trị âm là 44.7%, gần với mức của S2. Đặc trưng `negative_dt_ratio`, cũng là đặc trưng được bộ phát hiện E1 lựa chọn với ngưỡng 0.25, vì thế phản ánh quy ước lưu trữ chứ không phản ánh thuộc tính của thẻ nhân bản. Khác biệt thứ hai liên quan đến cửa sổ ghép cặp: tệp S3 chỉ chứa các cặp đọc chéo có |Δ| ≤ 5 ms, còn tệp S2 ghép các cặp cách nhau tới 760 ms. Các đặc trưng mô tả độ lớn và độ phân tán của Δ, cùng với số cặp va chạm, do đó khác nhau theo cấu trúc; `small_dt_10ms_ratio` của S3 bằng 1.000 ở mọi phiên, trong khi dữ liệu thô của S2 vẫn có 4.8% cặp đọc chéo nằm trong khoảng 5 ms. Khác biệt thứ ba là định nghĩa của `read_count`. Ở lớp thật, đây là tổng số lượt đọc của một phiên S1, vốn được ấn định bởi kế hoạch thí nghiệm (100 hoặc 150 lượt); ở lớp nhân bản, đây là số cặp đọc trùng trong tệp S3 (50–83 cặp). Khác biệt cuối cùng là độ phân giải thời gian: 93.8% giá trị Δ của S3 nằm trên lưới mili-giây nguyên, trong khi Δ của S2 có độ phân giải micro-giây, dẫn đến chênh lệch ở tỷ lệ Δ bằng 0.

Bảng 4.y. Các cơ chế tạo khả năng phân tách và tỷ trọng quy kết SHAP tương ứng

| Cơ chế | Đặc trưng liên quan | Lớp thật | Lớp nhân bản | Tỷ trọng \|SHAP\| (%) |
|---|---|---|---|---|
| Quy ước dấu (S2 lưu Δ có dấu, S3 lưu \|Δ\|) | `negative_dt_ratio`, `positive_dt_ratio`, `dt_min`, `dt_mean`, `dt_median` | `negative_dt_ratio` ≈ 0.50 | `negative_dt_ratio` = 0.00 | 26.6 |
| Cửa sổ ghép cặp (S3: ≤ 5 ms; S2: ≤ 760 ms) | `dt_std`, `dt_max`, `dt_abs_mean`, `dt_abs_median`, `small_dt_10ms_ratio`, `small_dt_50ms_ratio`, `collision_count` | `dt_max`: 0.33–0.76 s; ~293 cặp/phiên | `dt_max` = 0.005 s; 50–83 cặp/phiên | 64.5 |
| Định nghĩa `read_count` | `read_count` | 100–154 | 50–83 | 8.7 |
| Độ phân giải thời gian | `zero_dt_ratio` | 0.000 | 0.000–0.176 | 0.1 |

Cộng dồn theo cơ chế, toàn bộ tỷ trọng quy kết SHAP của mô hình E3 thuộc về các đặc trưng chịu ảnh hưởng của những khác biệt nêu trên, trong đó cửa sổ ghép cặp chiếm 64.5% và quy ước dấu chiếm 26.6%. Các khác biệt này có thể gắn với quá trình sinh dữ liệu của từng kịch bản. Các phiên S1 được ghi trên phần cứng trong năm ngày, từ ngày 4 đến ngày 9/11/2025. Các phiên S2 nằm trong khoảng 5.6 phút theo đồng hồ hệ thống, mỗi phiên kéo dài khoảng 37 giây. Trong khi đó, toàn bộ 108 phiên S3 nằm trong khoảng 6 giây (10:38:05.6–10:38:11.9 ngày 11/11/2025), mỗi phiên có đúng 300 sự kiện và phần micro-giây của các mốc thời gian chỉ nhận 39 giá trị khác nhau, so với 1 000 giá trị ở S1 và S2. Những đặc điểm này phù hợp với giả thuyết rằng lớp nhân bản được sinh bằng phần mềm, một khả năng đã được nêu trong tài liệu mô tả bộ dữ liệu.

Kết quả trên cần được đặt trong mối liên hệ với giao thức đánh giá ở mục 3.5. Trong cài đặt ban đầu, nhãn nhóm được trích từ `session_id` theo mẫu "TAG". Do mã phiên của S3 (chẳng hạn `S20251110_S3_P10_run1`) không chứa mẫu này, mỗi phiên S3 bị xem là một nhóm riêng, nên dữ liệu có 120 nhóm thay vì 12. Sau khi ánh xạ các phiên S3 về thẻ vật lý dựa trên kế hoạch thí nghiệm (`s3_plan.csv`), dữ liệu còn 12 nhóm, mỗi nhóm chứa cả hai lớp, và tập kiểm tra gồm 54 mẫu. Với phép chia đã hiệu chỉnh, cả RF và SVM vẫn đạt độ chính xác 1.000 ở cả năm hạt giống. Như vậy, việc mô hình ghi nhớ danh tính thẻ không đủ để giải thích kết quả; khả năng phân tách nhiều khả năng bắt nguồn từ khác biệt trong quá trình xây dựng dữ liệu, một dạng rò rỉ thông tin mà phép chia theo nhóm không kiểm soát được (Kaufman và cộng sự, 2012; Kapoor và Narayanan, 2023).

### 4.5.4. Phân tích độ nhạy với quy trình dẫn xuất đồng nhất

Để tách tín hiệu có ý nghĩa an ninh khỏi ảnh hưởng của khâu tiền xử lý, các đặc trưng giao thức được tính lại từ sự kiện đọc thô của S2 và S3 theo cùng một quy tắc. Với mỗi lượt đọc của reader A, lượt đọc gần nhất của reader B được xác định và hiệu có dấu Δ = t_B − t_A được tính; cả hai lớp được đưa về cùng lưới thời gian 1 ms và sử dụng chung cửa sổ đồng hiện diện w = 5 ms. Chúng tôi bổ sung một đại lượng chuẩn hóa theo tốc độ đọc. Nếu hai reader đọc độc lập theo quá trình Poisson, xác suất để một lượt đọc của A có lượt đọc của B trong cửa sổ w là p₀ = 1 − exp(−2wλ_B), với λ_B là tốc độ đọc của reader B. Tỷ số giữa tần suất đồng hiện diện quan sát được và p₀ biểu thị mức đồng bộ vượt quá mức ngẫu nhiên.

Bảng 4.z. Đặc trưng sau khi dẫn xuất đồng nhất (trung vị theo phiên)

| Đặc trưng | Lớp thật (S2) | Lớp nhân bản (S3) | AUC đơn biến |
|---|---|---|---|
| Tỷ lệ Δ âm trong cửa sổ | 0.458 | 0.433 | 0.546 |
| Tỷ lệ Δ = 0 | 0.083 | 0.107 | 0.602 |
| Tần suất đồng hiện diện (≤ 5 ms) | 0.103 | 0.447 | 1.000 |
| Trung vị \|Δ\| giữa hai reader (ms) | 31 | 6 | 1.000 |
| Tốc độ đọc (Hz) | 7.9 | 50.3 | 1.000 |
| Xác suất trùng hợp ngẫu nhiên p₀ | 0.039 | 0.222 | – |
| Tỷ số đồng hiện diện so với p₀ | 2.69 | 2.01 | 0.834ᵃ |
| Tỷ số \|Δ\| quan sát so với \|Δ\| kỳ vọng | 0.36 | 0.44 | – |
| Số lượt đọc mỗi reader | 147.25 | 150.00 | 1.000 |

ᵃ Giá trị cao hơn ở lớp thật.

Khi hai lớp được xử lý theo cùng một quy tắc, các đặc trưng liên quan đến dấu và độ phân giải gần như mất khả năng phân tách: AUC của tỷ lệ Δ âm giảm từ 1.000 xuống 0.546, và của tỷ lệ Δ bằng 0 giảm xuống 0.602. Theo đó, bộ phát hiện E1 sẽ hoạt động gần với mức ngẫu nhiên nếu dữ liệu hai lớp được tiền xử lý thống nhất.

Tần suất đồng hiện diện và khoảng cách thời gian giữa hai reader vẫn phân tách được hai lớp ở dạng thô. Định danh nhân bản xuất hiện đồng thời ở hai reader trong 44.7% lượt đọc, so với 10.3% ở lớp thật, với trung vị |Δ| lần lượt là 6 ms và 31 ms. Tuy vậy, tốc độ đọc trong S3 cao gấp khoảng 6.4 lần S2 (50.3 Hz so với 7.9 Hz), nên xác suất hai lượt đọc độc lập rơi vào cùng một cửa sổ 5 ms cũng cao hơn khoảng 5.7 lần (0.222 so với 0.039). Sau khi chuẩn hóa theo mức ngẫu nhiên, cả hai lớp đều thể hiện mức đồng bộ vượt ngẫu nhiên, nhưng mức vượt ở lớp thật (2.69 lần) cao hơn ở lớp nhân bản (2.01 lần), và tỷ số giữa |Δ| quan sát và |Δ| kỳ vọng cũng thấp hơn ở lớp thật (0.36 so với 0.44). Điều này phù hợp với điều kiện vật lý của S2, trong đó hai reader cùng đọc một thẻ thật nằm trong vùng phủ sóng chồng lấn.

Các đặc trưng còn giữ AUC bằng 1.000 sau khi dẫn xuất đồng nhất gồm tốc độ đọc, thời lượng phiên và số lượt đọc mỗi reader; ở chỉ số cuối, S3 luôn đạt đủ 150 lượt, trong khi S2 có lượt đọc hụt. Khi chỉ sử dụng các đặc trưng đã dẫn xuất đồng nhất và đánh giá bằng kiểm định chéo sáu phần theo nhóm thẻ, RF vẫn đạt độ chính xác 1.000, với độ quan trọng tập trung vào trung vị |Δ| (0.48) và số lượt đọc mỗi reader (0.41). Cả hai đại lượng này đều phụ thuộc trực tiếp vào nhịp đọc của từng kịch bản.

### 4.5.5. Diễn giải dưới góc độ an ninh

Bảng 4.w. Đối chiếu các bằng chứng an ninh giả thuyết với kết quả trên RFID-ExSim

| Bằng chứng giả thuyết (mục 3.3) | Chiều kỳ vọng | Kết quả quan sát |
|---|---|---|
| Số reader cùng đọc một UID | Tăng → rủi ro nhân bản tăng | Xuất hiện ở cả hai lớp, do S2 gồm hai reader đọc hợp lệ cùng một thẻ |
| Khoảng cách thời gian giữa hai reader | Gần 0 → rủi ro nhân bản tăng | Đúng chiều ở dạng thô; đảo chiều sau khi chuẩn hóa theo tốc độ đọc |
| Chuyển tiếp reader bất khả thi | Tăng → rủi ro nhân bản tăng | Không xác định được do thiếu thông tin vị trí reader; vùng phủ của hai reader chồng lấn |
| Mức đầy đủ của luồng đọc | Quá đều đặn → nghi ngờ dữ liệu bị chèn | S3 không có lượt đọc hụt; không tách được khỏi đặc tính của quá trình mô phỏng |
| Dấu và phân phối của Δ (E1) | – | Phát sinh từ quy ước lưu trữ |

Đối chiếu với các giả thuyết ở mục 3.3 (Bảng 4.w) cho thấy, trên RFID-ExSim và với quy trình xây dựng đặc trưng hiện tại, các bộ phát hiện chưa sử dụng bằng chứng an ninh theo nghĩa mà thiết kế nghiên cứu hướng tới. Khả năng phân loại của chúng chủ yếu dựa trên khác biệt trong cách từng lớp được ghi nhận, tóm tắt và sinh ra.

Kết quả này góp phần giải thích hiện tượng trần ở mục 4.2–4.3. Hiệu năng tuyệt đối ở cả ba cấu hình và cả hai bộ phân loại là hệ quả của việc hai lớp đã tách biệt ngay từ khâu xây dựng dữ liệu, do đó chưa thể được xem là bằng chứng ủng hộ RQ1. Đối với RQ2, ngoài hiện tượng bão hòa, mỗi mẫu lớp thật trong E3 được ghép từ hai thí nghiệm khác nhau: đặc trưng giao thức lấy từ một phiên S2, còn `read_count` lấy từ một phiên S1 theo thứ tự tương ứng. Không mẫu nào trong 108 mẫu lớp thật có hai họ bằng chứng thu từ cùng một lần quan sát, nên câu hỏi về lợi ích của việc kết hợp bằng chứng chưa được kiểm định trong thiết lập hiện tại.

Phân tích độ nhạy cũng cho thấy sự đồng hiện diện của một UID tại nhiều reader, tự nó, không đủ để kết luận về hành vi nhân bản, bởi một thẻ thật nằm trong vùng phủ chồng lấn tạo ra cùng một mẫu hình. Sự đồng hiện diện chỉ trở thành bằng chứng khi đi kèm một ràng buộc không gian, chẳng hạn hai reader có vùng đọc không giao nhau, hoặc hai điểm kiểm soát cách nhau một thời gian di chuyển tối thiểu. Theo cách hiểu này, bằng chứng về nhân bản mang tính quan hệ giữa danh tính, bố trí reader và thời gian, hơn là một thống kê nội tại của từng phiên đọc. Đây cũng là lý do đặc trưng chuyển tiếp bất khả thi chưa thể được xác định trên RFID-ExSim, vì tính bất khả thi của một chuyển tiếp chỉ có nghĩa khi vị trí của các reader đã được biết.

Xét theo mô hình đối thủ ở mục 3.1, một bộ phát hiện dựa vào nhịp đọc và mức đầy đủ của luồng đọc có thể bị vượt qua nếu kẻ tấn công tạo ra luồng đọc có đặc điểm thời gian tương tự thẻ thật. Khả năng này nằm trong tầm kiểm soát của một đối thủ đã sao chép được UID, bởi đối thủ đó cũng quyết định thời điểm và cách thức trình diện thẻ nhân bản. Kết quả hiện tại vì vậy chưa cho phép đưa ra nhận định về khả năng chống chịu trước đối thủ thích nghi. Nhận định rằng một UID hợp lệ chưa đủ để xác lập danh tính tin cậy vẫn đứng vững, song bằng chứng hành vi dùng để bổ sung cho UID cần được xây dựng ở mức quan hệ và được kiểm soát theo nhịp đọc.

Những kết quả trên gợi ý một số yêu cầu đối với việc đánh giá bộ phát hiện nhân bản dựa trên học máy. Đặc trưng của mọi lớp cần được dẫn xuất từ sự kiện thô thông qua cùng một quy trình, với cùng quy ước dấu, cửa sổ ghép cặp và độ phân giải thời gian, và kết quả truy xuất nguồn gốc đặc trưng như Bảng 4.y nên được báo cáo cùng kết quả phân loại. Bằng chứng giao thức nên được biểu diễn dưới dạng chuẩn hóa theo tốc độ đọc thay vì thống kê thô của Δ. Dữ liệu cần kèm thông tin bố trí reader để đặc trưng chuyển tiếp bất khả thi có định nghĩa vận hành, và lớp nhân bản cần được thu trên phần cứng hoặc được sinh với nhịp đọc và tỷ lệ đọc hụt tương đương thẻ thật. Các vấn đề này được thảo luận thêm ở mục 5.3 và 5.4.

### Tài liệu tham khảo (cho mục 4.5)

Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32.

Geirhos, R., Jacobsen, J.-H., Michaelis, C., Zemel, R., Brendel, W., Bethge, M., & Wichmann, F. A. (2020). Shortcut learning in deep neural networks. *Nature Machine Intelligence*, 2(11), 665–673.

Hooker, G., Mentch, L., & Zhou, S. (2021). Unrestricted permutation forces extrapolation: Variable importance requires at least one more model, or there is no free variable importance. *Statistics and Computing*, 31(6), 82.

Kapoor, S., & Narayanan, A. (2023). Leakage and the reproducibility crisis in machine-learning-based science. *Patterns*, 4(9), 100804.

Kaufman, S., Rosset, S., Perlich, C., & Stitelman, O. (2012). Leakage in data mining: Formulation, detection, and avoidance. *ACM Transactions on Knowledge Discovery from Data*, 6(4), Article 15.

Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems*, 30.

Lundberg, S. M., Erion, G., Chen, H., DeGrave, A., Prutkin, J. M., Nair, B., Katz, R., Himmelfarb, J., Bansal, N., & Lee, S.-I. (2020). From local explanations to global understanding with explainable AI for trees. *Nature Machine Intelligence*, 2(1), 56–67.

Strobl, C., Boulesteix, A.-L., Zeileis, A., & Hothorn, T. (2007). Bias in random forest variable importance measures: Illustrations, sources and a solution. *BMC Bioinformatics*, 8, 25.

---

Tái lập số liệu:

```bash
export RFID_DATA=/path/to/RFID-ExSim-dataset/rfid_dataset/rfid_dataset
cd rfid_clone_detection/analysis_4_5
python replicate_team.py && python diagnose_team.py && python importance_team.py && python harmonize.py
```
