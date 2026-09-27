# 4.5. Feature Importance and Security Interpretation

> Số liệu trong mục này được tái lập từ notebook `RFID_Evidence_Ablation_Colab_1.ipynb`
> của nhóm (đã khớp output lưu trong notebook: 216 mẫu, 120 group, tập test 32
> mẫu = 9 Real / 23 Clone, mọi chỉ số = 1.000) và các script trong
> `analysis_4_5/`. Cách chạy lại ở cuối mục.

## Mở đầu mục (đoạn dẫn)

Các mục 4.2–4.3 cho thấy cả ba cấu hình bằng chứng (E1, E2, E3) và cả hai bộ
phát hiện (RF, SVM) đều đạt Accuracy, Precision, Recall và F1 bằng 1.000 trên
tập test giữ riêng. Khi mọi cấu hình cùng chạm trần, phép so sánh ablation không
còn phân biệt được đóng góp của từng nguồn bằng chứng: E3 − E2 = 0 không có
nghĩa là protocol evidence "không giúp gì", mà chỉ có nghĩa là phép đo đã bão
hòa. Vì vậy, phân tích độ quan trọng đặc trưng trở thành công cụ duy nhất còn
lại để trả lời câu hỏi cốt lõi của RQ1–RQ2: **detector thực sự dựa vào bằng
chứng nào để gắn nhãn một định danh là "cloned"?** Mục tiêu của phần này vì
thế không phải xếp hạng đặc trưng, mà là kiểm tra xem các đặc trưng được mô
hình sử dụng có mang nghĩa bảo mật hay không — tức là phân biệt giữa bằng
chứng an ninh (security evidence) và lối tắt do cách dựng dữ liệu (construction
shortcut).

## 4.5.1. Quy trình quy kết (attribution protocol)

Phân tích dùng mô hình Random Forest của cấu hình E3 (13 đặc trưng protocol +
`read_count`), vì đây là cấu hình chứa đầy đủ cả hai họ bằng chứng. Ba phương
pháp quy kết được dùng song song vì mỗi phương pháp có một điểm mù đã biết:

1. **Impurity importance** (mean decrease in Gini): nhanh nhưng thiên lệch khi
   các đặc trưng tương quan với nhau.
2. **Permutation importance trên tập test** (mức giảm F1 khi xáo trộn một cột):
   đo tác động thực trên dữ liệu chưa thấy, nhưng bằng 0 khi thông tin của cột
   bị xáo trộn đã có sẵn ở các cột khác.
3. **SHAP (TreeExplainer)**: phân bổ đóng góp theo từng mẫu, cho phép đọc cả độ
   lớn (mean |SHAP|) lẫn chiều tác động.

Toàn bộ quy trình được lặp lại với 5 seed (42, 7, 123, 2024, 99), mỗi seed tạo
một phép chia group-aware mới, để đo độ ổn định của thứ hạng.

Bổ sung cho ba phương pháp trên, nhóm thực hiện hai phân tích mà các nghiên cứu
dùng feature importance thường bỏ qua: (i) **kiểm toán nguồn gốc (provenance
audit)** — truy ngược từng đặc trưng về cách nó được tính cho mỗi lớp; và (ii)
**tái dẫn xuất đồng nhất (harmonised re-derivation)** — tính lại các đặc trưng
protocol từ sự kiện thô của S2 và S3 bằng một quy tắc duy nhất, để kiểm tra
đặc trưng nào vẫn còn phân tách được khi mọi khác biệt về cách xử lý dữ liệu bị
loại bỏ.

## 4.5.2. Detector dựa vào đặc trưng nào?

**Bảng 4.x — Độ quan trọng đặc trưng của RF trong E3 (trung bình ± SD qua 5 seed)**

| Đặc trưng | Impurity | mean \|SHAP\| | Thứ hạng SHAP (tốt nhất – kém nhất) | Giảm F1 khi hoán vị | AUC đơn biến |
|---|---|---|---|---|---|
| `dt_abs_mean` | 0.097 ± 0.013 | 0.048 ± 0.006 | 1 – 10 | 0.000 | 1.000 |
| `dt_max` | 0.096 ± 0.013 | 0.048 ± 0.006 | 1 – 9 | 0.000 | 1.000 |
| `positive_dt_ratio` | 0.095 ± 0.008 | 0.048 ± 0.004 | 2 – 8 | 0.000 | 1.000 |
| `small_dt_50ms_ratio` | 0.095 ± 0.008 | 0.048 ± 0.004 | 2 – 7 | 0.000 | 1.000 |
| `dt_abs_median` | 0.095 ± 0.007 | 0.047 ± 0.004 | 1 – 7 | 0.000 | 1.000 |
| `dt_std` | 0.094 ± 0.017 | 0.047 ± 0.009 | 1 – 11 | 0.000 | 1.000 |
| `collision_count` | 0.091 ± 0.013 | 0.046 ± 0.006 | 3 – 11 | 0.000 | 1.000 |
| `read_count` | 0.087 ± 0.017 | 0.044 ± 0.009 | 2 – 11 | 0.000 | 1.000 |
| `negative_dt_ratio` | 0.084 ± 0.006 | 0.042 ± 0.003 | 5 – 10 | 0.000 | 1.000 |
| `dt_min` | 0.081 ± 0.012 | 0.041 ± 0.006 | 3 – 10 | 0.000 | 1.000 |
| `small_dt_10ms_ratio` | 0.077 ± 0.009 | 0.039 ± 0.004 | 7 – 11 | 0.000 | 1.000 |
| `dt_median` | 0.004 ± 0.006 | 0.002 ± 0.003 | 12 – 14 | 0.000 | 0.973 |
| `dt_mean` | 0.001 ± 0.003 | 0.001 ± 0.001 | 12 – 14 | 0.000 | 0.910 |
| `zero_dt_ratio` | 0.001 ± 0.001 | 0.001 ± 0.001 | 12 – 14 | 0.000 | 0.944 |

Ba quan sát rút ra từ Bảng 4.x:

- **Độ quan trọng phân bố gần như đều** trên 11 đặc trưng (impurity 0.077–0.097),
  không có đặc trưng nào chiếm ưu thế rõ rệt.
- **Thứ hạng không ổn định**: cùng một đặc trưng có thể đứng thứ 1 ở seed này và
  thứ 11 ở seed khác (ví dụ `dt_std`, `collision_count`, `read_count`).
- **Permutation importance bằng 0 cho cả 14 đặc trưng**, dù mô hình phân loại
  đúng tuyệt đối.

Cả ba quan sát có chung một nguyên nhân: **11 trên 14 đặc trưng, khi đứng một
mình, đã tách hoàn toàn hai lớp** (AUC đơn biến = 1.000, khoảng giá trị của
Real và Clone không chồng lấn). Khi có 11 đặc trưng dư thừa và mỗi cái đều đủ
để phân loại, RF chọn ngẫu nhiên giữa chúng ở mỗi lần tách nút (nên độ quan
trọng chia đều và thứ hạng dao động theo seed), và xáo trộn một cột bất kỳ không
làm giảm hiệu năng vì 10 cột còn lại bù được (nên permutation importance bằng
0). Nói cách khác, thứ hạng trong Bảng 4.x **không trả lời được** detector dựa
vào bằng chứng nào: nó chỉ cho thấy có rất nhiều con đường tương đương để tách
hai lớp. Để trả lời câu hỏi, cần hỏi vì sao các đặc trưng này lại tách hoàn
hảo như vậy.

## 4.5.3. Kiểm toán nguồn gốc đặc trưng

Truy ngược từng đặc trưng về dữ liệu gốc cho thấy sự phân tách đến từ bốn cơ
chế, cả bốn đều nằm ở khâu dựng dữ liệu chứ không nằm ở hành vi của thẻ clone
(Bảng 4.y).

**Bảng 4.y — Cơ chế tạo ra sự phân tách của các đặc trưng trong E1/E2/E3**

| Cơ chế | Đặc trưng bị ảnh hưởng | Real (S2 / S1) | Clone (S3) | Tỷ trọng SHAP |
|---|---|---|---|---|
| **Quy ước dấu**: S2 lưu `dt = tB − tA` có dấu; S3 lưu `delta_ms = \|tB − tA\|` | `negative_dt_ratio`, `positive_dt_ratio`, `dt_min`, `dt_mean`, `dt_median` | `negative_dt_ratio` ≈ 0.50 | `negative_dt_ratio` = 0.00 | 26.6% |
| **Cửa sổ ghép cặp**: file S3 chỉ giữ các cặp có \|Δ\| ≤ 5 ms; file S2 ghép cặp tới 760 ms | `dt_std`, `dt_max`, `dt_abs_mean`, `dt_abs_median`, `small_dt_10/50ms_ratio`, `collision_count` | `dt_max` 0.33–0.76 s; ~293 cặp/phiên | `dt_max` = 0.005 s; 50–83 cặp/phiên | 64.5% |
| **Định nghĩa khác nhau**: `read_count` của Real = tổng lượt đọc của S1 (do kế hoạch thí nghiệm đặt là 100 hoặc 150); của Clone = số cặp va chạm trong file S3 | `read_count` | 100–154 | 50–83 | 8.7% |
| **Độ phân giải thời gian**: 93.8% giá trị S3 nằm trên lưới mili-giây nguyên; S2 có độ phân giải micro-giây | `zero_dt_ratio` | 0.000 | 0.000–0.176 | 0.1% |

Hai kiểm chứng trực tiếp khẳng định cơ chế thứ nhất và thứ hai. Thứ nhất, khi
tính lại hiệu `tB − tA` **có dấu** từ chính timestamp của file S3, tỷ lệ giá
trị âm là 44.7% — gần như bằng mức ≈ 50% của S2. Đặc trưng `negative_dt_ratio`,
cũng chính là đặc trưng mà detector E1 tự chọn (ngưỡng 0.25), vì vậy không đo
một thuộc tính nào của thẻ clone: nó chỉ phản ánh việc một file lưu giá trị
tuyệt đối còn file kia thì không. Thứ hai, `small_dt_10ms_ratio` của S3 bằng
đúng 1.000 ở mọi phiên vì file tóm tắt S3 chỉ chứa các cặp trong cửa sổ 5 ms;
trong dữ liệu thô của S2 vẫn có 4.8% cặp đọc chéo nằm trong 5 ms.

Cộng tỷ trọng SHAP theo cơ chế, **100% khối lượng quy kết của mô hình E3 rơi
vào các đặc trưng mà khả năng phân tách của chúng có thể truy về lựa chọn xử
lý dữ liệu**. Bên dưới các cơ chế này còn một nhân tố bao trùm là **quá trình
sinh dữ liệu (data-generating process)**: 108 phiên S1 được thu trên phần cứng
trong 5 ngày (4–9/11/2025); 108 phiên S2 nằm trong khoảng 5.6 phút đồng hồ thực,
mỗi phiên khoảng 37 giây; còn 108 phiên S3 nằm gọn trong khoảng 6 giây đồng hồ
thực (10:38:05.6 → 10:38:11.9 ngày 11/11/2025), mỗi phiên đúng 300 sự kiện
(150 mỗi reader) và phần micro-giây của timestamp chỉ có 39 giá trị khác nhau
(so với 1 000 ở S1 và S2). Các dấu hiệu này phù hợp với việc S3 được sinh bằng
phần mềm — điều mà tài liệu dataset cho phép ("…a pair of distinct tags is
assigned the same logical UID within metadata to simulate ambiguity") và tên
"RFID-ExSim" gợi ý.

Cần nhấn mạnh rằng giao thức group-aware ở mục 3.5 **đã làm đúng nhiệm vụ của
nó**, nhưng nhiệm vụ đó khác với vấn đề phát hiện ở đây. Notebook dùng
`extract_tag()` để lấy tên tag từ `session_id`; do `session_id` của S3 (ví dụ
`S20251110_S3_P10_run1`) không chứa chuỗi "TAG", mỗi phiên S3 trở thành một
group riêng (tổng cộng 120 group = 12 tag Real + 108 phiên Clone). Khi ánh xạ
lại S3 về tag vật lý qua `s3_plan.csv` (P1–P3 → TAG01, …), dữ liệu còn 12 group,
mỗi group chứa cả hai lớp, và tập test tăng lên 54 mẫu. Với cách chia đã sửa
này, cả RF và SVM vẫn đạt accuracy 1.000 ở cả 5 seed. Như vậy, **việc mô hình
"nhớ" danh tính thẻ đã bị loại trừ như một lời giải thích** — và chính vì loại
trừ được nó, các cơ chế dựng dữ liệu trong Bảng 4.y còn lại là lời giải thích
hợp lý duy nhất. Đây là một dạng rò rỉ khác với rò rỉ danh tính: rò rỉ do cách
dựng dữ liệu (construction leakage), nảy sinh khi các lớp được tạo bởi các quy
trình xử lý khác nhau. Chia theo group không phát hiện được loại rò rỉ này.

## 4.5.4. Tái dẫn xuất đồng nhất: bằng chứng nào còn đứng vững?

Để tách tín hiệu bảo mật khỏi tác động của khâu xử lý, các đặc trưng protocol
được tính lại từ sự kiện thô (`rfid_dataset_S2_all.jsonl`,
`rfid_dataset_S3_all.jsonl`) theo một quy tắc duy nhất cho cả hai lớp: với mỗi
lần đọc của reader A, lấy lần đọc gần nhất của reader B, tính Δ = tB − tA có
dấu, đưa cả hai lớp về cùng lưới 1 ms, và dùng chung cửa sổ đồng hiện diện 5 ms.
Ngoài ra, nhóm đưa vào một đại lượng chuẩn hóa theo tốc độ đọc: xác suất trùng
hợp ngẫu nhiên nếu hai reader đọc độc lập theo quá trình Poisson là
p₀ = 1 − exp(−2wλ_B), với w = 5 ms và λ_B là tốc độ đọc của reader B. Chia tỷ
lệ đồng hiện diện quan sát được cho p₀ cho biết mức đồng bộ **vượt quá mức ngẫu
nhiên**.

**Bảng 4.z — Đặc trưng sau khi tái dẫn xuất đồng nhất (trung vị theo phiên, S2 Real vs S3 Clone)**

| Đặc trưng | Real (S2) | Clone (S3) | AUC đơn biến | Diễn giải |
|---|---|---|---|---|
| Tỷ lệ Δ âm trong cửa sổ | 0.458 | 0.433 | 0.546 | Sụp về mức ngẫu nhiên (trước đó 1.000) |
| Tỷ lệ Δ = 0 | 0.083 | 0.107 | 0.602 | Sụp về gần ngẫu nhiên |
| Tỷ lệ đồng hiện diện ≤ 5 ms | 0.103 | 0.447 | 1.000 | Tách được ở dạng thô |
| Trung vị \|Δ\| giữa hai reader (ms) | 31 | 6 | 1.000 | Tách được ở dạng thô |
| Tốc độ đọc (Hz) | 7.9 | 50.3 | 1.000 | Khác biệt về nhịp sinh dữ liệu |
| Mức trùng hợp ngẫu nhiên p₀ | 0.039 | 0.222 | — | Hệ quả của tốc độ đọc |
| **Đồng hiện diện / mức ngẫu nhiên** | **2.69×** | **2.01×** | 0.834 (ngược chiều) | Real đồng bộ **cao hơn** Clone |
| **\|Δ\| quan sát / \|Δ\| kỳ vọng ngẫu nhiên** | **0.36** | **0.44** | — | Real sát nhau **hơn** Clone |
| Số lượt đọc mỗi reader | 147.25 | 150.00 | 1.000 | S3 không bao giờ đọc hụt |

Bảng 4.z tách các đặc trưng thành ba nhóm với ba kết luận khác nhau.

**(a) Các đặc trưng do quy ước và độ phân giải biến mất.** Tỷ lệ Δ âm giảm từ
AUC 1.000 xuống 0.546, tỷ lệ Δ = 0 giảm xuống 0.602. Detector E1 — vốn được
chọn vì là "bằng chứng protocol mạnh nhất" — sẽ gần như đoán ngẫu nhiên nếu dữ
liệu hai lớp được xử lý giống nhau.

**(b) Tín hiệu đồng hiện diện có vẻ tồn tại, nhưng không vượt qua phép chuẩn hóa.**
Ở dạng thô, định danh clone xuất hiện đồng thời ở hai reader thường xuyên hơn
(44.7% so với 10.3%) và sát nhau hơn (6 ms so với 31 ms). Kết quả này thoạt
nhìn khớp với trực giác "Multiple Readers/UID ↑ → Clone Risk ↑". Tuy nhiên,
reader trong S3 đọc nhanh gấp 6.4 lần (50.3 Hz so với 7.9 Hz), nên xác suất hai
lần đọc tình cờ rơi vào cùng 5 ms cũng cao gấp khoảng 5.7 lần (0.222 so với
0.039). Sau khi chuẩn hóa, cả hai lớp đều đồng bộ hơn mức ngẫu nhiên, và **lớp
Real (S2) còn đồng bộ hơn lớp Clone** (2.69× so với 2.01×; khoảng cách |Δ| so với
kỳ vọng ngẫu nhiên là 0.36 so với 0.44). Điều này hợp lý về mặt vật lý: trong
S2, hai reader đọc cùng một thẻ thật nằm trong vùng phủ sóng chồng lấn, nên sự
đồng hiện diện là hành vi hợp lệ.

**(c) Những gì còn phân tách hoàn hảo đều thuộc về nhịp sinh dữ liệu.** Các đặc
trưng vẫn đạt AUC = 1.000 sau khi tái dẫn xuất là tốc độ đọc, thời lượng phiên
và mức "đầy đủ" (S3 luôn đạt đúng 150/150 lượt đọc mỗi reader, trong khi S2 có
đọc hụt). Ngay cả khi RF chỉ được dùng các đặc trưng đã đồng nhất (đánh giá bằng
leave-tags-out theo 12 tag), mô hình vẫn đạt accuracy 1.000, và độ quan trọng
tập trung vào trung vị |Δ| (0.48) cùng số lượt đọc mỗi reader (0.41). Như (b) đã
chỉ ra, cả hai đại lượng này đều phụ thuộc trực tiếp vào nhịp đọc.

## 4.5.5. Diễn giải an ninh: detector dựa vào bằng chứng an ninh nào?

Đối chiếu kết quả với khung bằng chứng đã đặt ra ở mục 3.3 (Bảng 4.w) cho câu
trả lời trực tiếp cho câu hỏi của mục này.

**Bảng 4.w — Bằng chứng an ninh kỳ vọng so với những gì quan sát được trên RFID-ExSim**

| Bằng chứng an ninh (giả thuyết) | Chiều kỳ vọng | Quan sát | Trạng thái |
|---|---|---|---|
| Multiple Readers per UID | ↑ → Clone Risk ↑ | Có ở **cả hai lớp**: S2 là hai reader đọc hợp lệ một thẻ thật | Không đặc thù cho clone |
| Khoảng cách thời gian giữa các reader (inter-reader Δ) | Gần 0 → Clone Risk ↑ | Ở dạng thô: đúng chiều. Sau chuẩn hóa theo tốc độ đọc: Real đồng bộ hơn Clone | Bị nhiễu bởi nhịp đọc |
| Impossible Reader Transition | ↑ → Clone Risk ↑ | **Không tính được**: dataset không có dữ liệu vị trí reader hay thời gian di chuyển tối thiểu, và hai reader có vùng phủ chồng lấn | Không xác định được |
| Read regularity / completeness | Luồng quá "hoàn hảo" → nghi ngờ bị chèn | S3 không bao giờ đọc hụt (150/150) | Không tách được khỏi đặc tính của bộ mô phỏng |
| Tín hiệu protocol dạng dấu và phân phối Δ (E1) | — | Do quy ước lưu dữ liệu tạo ra | Không phải bằng chứng an ninh |

Từ đó, câu trả lời cho câu hỏi "detector dựa vào bằng chứng an ninh nào để phát
hiện cloned identity?" là: **trên RFID-ExSim và với quy trình dựng đặc trưng
hiện tại, detector không dựa vào bằng chứng an ninh nào mà thiết kế nghiên cứu
dự định.** Nó dựa vào những khác biệt về cách từng lớp được ghi nhận, tóm tắt
và sinh ra. Kết luận này không làm yếu bài báo. Ngược lại, nó là kết quả quan
trọng nhất của phần diễn giải, vì ba lý do.

**Thứ nhất, nó giải thích hiện tượng trần ở 4.2–4.3.** Hiệu năng 1.000 đồng
loạt ở E1, E2, E3 và cả hai bộ phát hiện không phải là bằng chứng rằng bài toán
đã được giải. Nó là hệ quả của việc hai lớp tách được ngay từ khi dựng dữ liệu.
Vì vậy, với RQ1, không thể kết luận rằng bằng chứng hành vi phát hiện được clone.
Với RQ2, câu hỏi "kết hợp bằng chứng có tốt hơn không" không kiểm định được trong
cấu hình hiện tại. Ngoài hiện tượng bão hòa, mỗi mẫu Real của E3 còn là một bản
ghép từ hai thí nghiệm khác nhau: đặc trưng protocol lấy từ một phiên S2, còn
`read_count` lấy từ một phiên S1 được ghép theo thứ tự (0/108 mẫu Real có hai
họ bằng chứng đến từ cùng một lần quan sát). Do đó E3 không mô tả việc kết hợp
bằng chứng trên cùng một định danh.

**Thứ hai, nó chỉ ra điều kiện để bằng chứng hành vi có ý nghĩa an ninh.** Phân
tích ở 4.5.4(b) cho thấy "cùng một UID xuất hiện ở nhiều reader cùng lúc" tự nó
không phải là dấu hiệu clone, vì một thẻ thật trong vùng phủ chồng lấn cũng tạo
ra đúng mẫu hình đó. Sự đồng hiện diện chỉ trở thành bằng chứng khi có **ràng
buộc không gian**: hai reader mà vùng đọc không thể cùng chạm tới một thẻ, hoặc
hai checkpoint cách nhau một khoảng thời gian di chuyển tối thiểu. Nói cách
khác, bằng chứng clone mang tính **quan hệ** (UID × topology reader × thời gian),
không phải một thống kê nội tại của một phiên đọc. Điều này cũng giải thích vì
sao "Impossible Reader Transition" — bằng chứng mạnh nhất về mặt lý thuyết —
chưa thể tính được: tính "bất khả thi" chỉ xác định được khi có mô hình vị trí
của reader.

**Thứ ba, nó có hệ quả trực tiếp về đối thủ (adversarial implication).** Một
detector học theo nhịp đọc, độ đầy đủ của luồng đọc và cách lưu Δ sẽ bị vượt
qua bởi bất kỳ kẻ tấn công nào tạo luồng đọc có nhịp giống thẻ thật. Khả năng
này không nằm ngoài tầm của mô hình đe dọa ở 3.1: kẻ tấn công đã sao chép được
UID thì cũng kiểm soát được thời điểm trình diện thẻ clone. Vì vậy, kết quả
hiện tại không cung cấp bảo đảm an ninh nào trước một kẻ tấn công thích nghi,
và nguyên tắc "UID Match ≠ Trusted Identity" (mục 5.2) vẫn đúng. Tuy nhiên, bằng
chứng hành vi thay thế cho UID phải là bằng chứng quan hệ và có kiểm soát nhịp
đọc, chứ không phải thống kê theo từng phiên.

## 4.5.6. Hệ quả cho các mục tiếp theo

- **Cho 4.6 (RQ3):** chi phí suy luận vẫn có thể báo cáo, nhưng cần gắn với nhận
  định rằng lợi ích an ninh tương ứng chưa được xác lập. Không nên trình bày
  cặp "hiệu năng 1.000 / suy luận nhanh" như một điểm cân bằng tốt.
- **Cho 5.3 (Limitations):** bổ sung ba giới hạn cụ thể: (i) hai lớp được tạo
  bởi các quy trình sinh và xử lý khác nhau (construction leakage); (ii) không
  có topology reader nên không tính được bằng chứng quan hệ; (iii) lớp Clone
  được sinh bằng phần mềm (S3 nằm trong 6 giây đồng hồ thực, timestamp trên
  lưới mili-giây).
- **Cho 5.4 (Future Work) / phiên bản sửa của thí nghiệm:**
  1. Tính mọi đặc trưng của cả hai lớp từ sự kiện thô qua **một** đoạn mã duy
     nhất (cùng quy ước dấu, cùng cửa sổ ghép cặp, cùng độ phân giải), và đưa
     bảng kiểm toán nguồn gốc (Bảng 4.y) vào phụ lục như một kiểm tra bắt buộc.
  2. Dùng đại lượng chuẩn hóa theo tốc độ đọc (mức đồng hiện diện vượt ngẫu
     nhiên) làm nguyên tố cho bằng chứng protocol, thay cho các thống kê Δ thô.
  3. Bổ sung metadata vị trí reader hoặc thiết kế kịch bản reader không chồng
     vùng phủ, để "Impossible Reader Transition" có định nghĩa vận hành.
  4. Thu thẻ clone trên phần cứng, hoặc tối thiểu sinh clone có nhịp đọc và tỷ
     lệ đọc hụt giống thẻ thật, rồi lặp lại toàn bộ phân tích 4.5. Nếu khi đó
     tín hiệu quan hệ vẫn phân tách được, nó mới là bằng chứng an ninh thực sự.

## Câu kết mục (có thể dùng nguyên văn)

Phân tích độ quan trọng đặc trưng cho thấy hiệu năng hoàn hảo của các detector
trên RFID-ExSim không bắt nguồn từ bằng chứng an ninh về hành vi của định danh
bị nhân bản, mà từ khác biệt trong cách mỗi lớp được sinh, ghép cặp và lưu
trữ. Sau khi đồng nhất quy trình dẫn xuất, các tín hiệu protocol mạnh nhất
biến mất, còn tín hiệu đồng hiện diện đa reader không vượt được mức giải thích
bởi nhịp đọc. Kết quả này xác định rõ điều kiện để bằng chứng hành vi có giá
trị an ninh: bằng chứng phải mang tính quan hệ giữa danh tính, vị trí reader và
thời gian, và phải được đánh giá trên các lớp có cùng quy trình sinh dữ liệu.

---

## Tái lập

```bash
export RFID_DATA=/path/to/RFID-ExSim-dataset/rfid_dataset/rfid_dataset
cd rfid_clone_detection/analysis_4_5
python replicate_team.py     # tái lập notebook của nhóm (216 mẫu, 120 group, test = 1.000)
python diagnose_team.py      # AUC đơn biến, kiểm toán dấu / cửa sổ / độ phân giải, lỗi group S3
python importance_team.py    # Bảng 4.x (impurity, SHAP, permutation, 5 seed) + chạy lại với group theo tag thật
python harmonize.py          # Bảng 4.z (tái dẫn xuất đồng nhất từ sự kiện thô + chuẩn hóa theo tốc độ đọc)
```
