# 4.5. Feature Importance and Security Interpretation

Nội dung dưới đây dùng số liệu **thật**, chạy từ `scripts/feature_importance.py`
trên chính train/test split leakage-safe của nhóm (E2 = Behavioral Only, E3 =
Combined). Có thể copy trực tiếp vào bài, chỉ cần thay số khi nhóm chạy lại
với dữ liệu/đặc trưng MB-MCM thật (hiện đang dùng bản proxy — xem README).

## Phương pháp (bắt buộc dùng ≥2 phương pháp, không chỉ 1)

Impurity importance (mặc định của `RandomForestClassifier.feature_importances_`)
**thiên vị khi các đặc trưng tương quan cao với nhau** — mà bộ đặc trưng của
nhóm chắc chắn tương quan (n_reads, duration_s, mean/std/max_inter_read_ms đều
là các cách đo khác nhau của cùng một hiện tượng: "mật độ đọc"). Vì vậy dùng
3 phương pháp bổ trợ nhau:

1. **Impurity importance** — nhanh, nhưng chỉ dùng để xếp hạng sơ bộ.
2. **Permutation importance** trên tập test — đo tác động thật khi "phá" một
   đặc trưng, ít thiên vị hơn nhưng **nhạy với đa cộng tuyến theo hướng ngược
   lại** (xem phát hiện quan trọng bên dưới).
3. **SHAP (TreeExplainer)** — vừa xếp hạng (mean |SHAP|) vừa cho **chiều tác
   động** (feature tăng thì risk tăng hay giảm), qua `corr(giá trị đặc trưng,
   SHAP value)` trên từng đặc trưng.

## Bảng kết quả

### E2 — Behavioral Only (Random Forest)

| Đặc trưng | Impurity | mean\|SHAP\| | Chiều tác động |
|---|---|---|---|
| `std_inter_read_ms` | 0.211 | 0.108 | risk ↓ khi tăng (yếu, r=-0.07) |
| `duration_s` | 0.193 | 0.099 | risk ↓ khi tăng (yếu, r=-0.08) |
| `n_reads` | 0.189 | 0.097 | **risk ↑ khi tăng** (r=+0.47) |
| `mean_inter_read_ms` | 0.184 | 0.095 | risk ↓ khi tăng (yếu, r=-0.08) |
| `max_inter_read_ms` | 0.147 | 0.074 | risk ↓ khi tăng (yếu, r=-0.08) |
| `reader_transition_rate` | 0.038 | 0.016 | **risk ↑ khi tăng** (r=+0.96) |
| `reader_transition_count` | 0.023 | 0.011 | **risk ↑ khi tăng** (r=+0.97) |
| `n_distinct_readers` | 0.016 | 0.009 | **risk ↑ khi tăng** (r=+0.96) |
| `distance_std`, `orientation_std`, `impossible_movement_*`, `success_rate` | 0.000 | 0.000 | không có sức phân biệt trong dataset hiện tại |

### E3 — Combined (Random Forest)

| Đặc trưng | Impurity | mean\|SHAP\| | Chiều tác động |
|---|---|---|---|
| `duration_s` | 0.143 | 0.072 | risk ↓ khi tăng (yếu, r=-0.08) |
| `mean_inter_read_ms` | 0.132 | 0.067 | risk ↓ khi tăng (yếu, r=-0.08) |
| `mb_min_cross_reader_delta_ms` | 0.130 | 0.066 | **risk ↑ khi giảm** (r=-0.61) |
| `mcm_suspicion_score` | 0.116 | 0.059 | **risk ↑ khi tăng** (r=+1.00) |
| `std_inter_read_ms` | 0.114 | 0.058 | risk ↓ khi tăng (yếu, r=-0.08) |
| `mcm_read_count_window` | 0.113 | 0.057 | **risk ↑ khi tăng** (r=+1.00) |
| `max_inter_read_ms` | 0.107 | 0.054 | risk ↓ khi tăng (yếu, r=-0.08) |
| `n_reads` | 0.105 | 0.054 | **risk ↑ khi tăng** (r=+0.49) |
| `mb_concurrent_reader_max` | 0.011 | 0.006 | **risk ↑ khi tăng** (r=+0.96) |
| `reader_transition_count/rate`, `n_distinct_readers`, `mb_duplicate_flag` | 0.005–0.009 | 0.003–0.004 | **risk ↑ khi tăng** (r≈+0.94–0.97), nhưng ảnh hưởng nhỏ khi đã có tín hiệu MCM liên tục |

*(Bảng đầy đủ + số thập phân chính xác: `results_4_5/feature_importance_E2_behavioral_only.csv`
và `..._E3_combined.csv`, sinh ra khi chạy script.)*

Biểu đồ: `results_4_5/shap_importance_E3.png` (đỏ = đẩy risk lên, xanh = kéo
risk xuống) — dùng minh hoạ, không phải trọng tâm của mục này.

## Trả lời câu hỏi chính: Detector dựa vào security evidence nào?

**Chuỗi bằng chứng chi phối cả E2 lẫn E3 là "mật độ đọc"**
(`n_reads`, `duration_s`, `*_inter_read_ms`) — chiếm ~70-80% tổng importance ở
cả hai config. Đứng sau là **reader-transition** (`n_distinct_readers`,
`reader_transition_count/rate`) và ở E3, **tín hiệu protocol liên tục**
(`mcm_suspicion_score`, `mcm_read_count_window`, `mb_min_cross_reader_delta_ms`)
— các tín hiệu rời rạc/nhị phân như `mb_duplicate_flag` đóng góp rất nhỏ.

Diễn giải theo đúng khung Thầy yêu cầu (Feature ↑ → Clone Risk ↑), **với chiều
đo được thật từ dữ liệu**, không chép nguyên ví dụ minh hoạ:

```
Multiple Readers per UID ↑            → Clone Risk ↑     (r = +0.96, mạnh)
Reader Transition (số lần/tỉ lệ) ↑    → Clone Risk ↑     (r = +0.94 – 0.97, mạnh)
Read Density (n_reads) ↑              → Clone Risk ↑     (r = +0.47 – 0.49, trung bình)
Protocol Suspicion Score (MCM) ↑      → Clone Risk ↑     (r = +1.00, gần như quyết định)
Cross-Reader Delta (MB) ↑             → Clone Risk ↓     (r = -0.61 — GẦN 0 mới đáng ngờ nhất)
```

**Lưu ý quan trọng — một điểm nhóm cần diễn giải đúng, KHÔNG chép máy móc ví
dụ của Thầy:** ví dụ minh hoạ "Inter-Read Time ↑ → Clone Risk ↑" mô tả một
kịch bản tổng quát (clone xuất hiện *cách xa* về thời gian). Trong dataset
hiện tại, S3 (cloned-proxy) được dựng bằng cách cho 2 reader đọc **dồn dập,
gần như liên tục** cùng UID — nên trong dữ liệu này chiều đo được là
**ngược lại**: inter-read time **càng ngắn** (đọc càng dồn dập) thì risk càng
cao (tương quan yếu -0.08, không mạnh bằng reader-transition nhưng vẫn cùng
chiều với read-density). Cần giải thích rõ trong bài: chiều tác động của một
đặc trưng phụ thuộc vào cách kịch bản tấn công được vận hành hoá trong
dataset, không phải một quy luật phổ quát — đây là điểm thể hiện nhóm hiểu
sâu chứ không chỉ chạy mô hình.

## Phát hiện quan trọng cần đưa vào bài: Permutation Importance ≈ 0 dù model hoàn hảo

Cột `permutation_importance_f1` bằng 0 cho **mọi** đặc trưng, kể cả những đặc
trưng có impurity/SHAP cao nhất. Đây **không phải lỗi code** — đây là hệ quả
trực tiếp của đa cộng tuyến: model đạt F1=1.0 trên test, và vì `n_reads`,
`duration_s`, `mean/std/max_inter_read_ms` cùng mang thông tin "mật độ đọc",
xáo trộn (permute) riêng lẻ một cột không đủ để phá vỡ quyết định — RF vẫn
dùng được các cột còn lại để bù. Đây là hạn chế đã biết của permutation
importance khi đặc trưng tương quan cao (nên dùng SHAP hoặc nhóm đặc trưng lại
trước khi permute). Nhóm nên trình bày phát hiện này như một **hạn chế về
phương pháp** ở 4.5, không nên chỉ báo cáo con số impurity/SHAP mà giấu đi sự
mâu thuẫn này — sẽ tăng độ tin cậy của phần phân tích rất nhiều.

## Đặc trưng "chết" (importance = 0): `distance_std`, `orientation_std`, `impossible_movement_*`, `success_rate`

Các đặc trưng này bằng 0 tuyệt đối ở CẢ 2 config — không phải vì chúng vô
dụng về mặt khái niệm, mà vì **trong dataset hiện tại, mỗi session chỉ có một
distance/orientation cố định** (do thiết kế thu thập theo `s1_plan.csv`/
`s3_plan.csv`: mỗi session ứng với đúng 1 tổ hợp distance×orientation×run) —
nên các đặc trưng "biến thiên trong session" luôn bằng 0, RF không có gì để
học. Đây là điểm cần ghi vào **Limitations (5.3)**: "Impossible Movement
Indicator" — đặc trưng lý thuyết rất hợp lý cho việc phát hiện clone (một tag
không thể đổi vị trí tức thời) — chưa được kiểm định trong nghiên cứu này vì
cách gộp theo session không tạo ra biến thiên nội-session; cần dữ liệu ở mức
window/sub-session (nhiều distance/orientation trong cùng 1 chuỗi đọc liên
tục) để đặc trưng này phát huy tác dụng, đây cũng là gợi ý cụ thể cho Future
Work (5.4).

## Liên hệ bảo mật (không chỉ là số liệu ML)

Vì tín hiệu chi phối là **mật độ đọc + số reader tham gia + protocol suspicion
score liên tục**, chứ không phải các dấu hiệu vật lý tinh vi (distance/
orientation không phân biệt được), nghĩa là: detector hiện tại **phát hiện
tốt một kiểu tấn công cụ thể** — attacker cố đọc/nhân bản UID bằng cách để 2
reader đọc dồn dập gần như đồng thời (gần với hành vi "flooding có định
hướng"). Một attacker tinh vi hơn — chỉ đọc lại UID **một lần**, ở **thời điểm
khác, tốc độ đọc bình thường**, không tạo mật độ đọc bất thường — nhiều khả
năng sẽ **né được** detector này, vì đúng những đặc trưng attacker cần né
(read density, reader transition) lại là những đặc trưng detector dựa vào
nhiều nhất. Đây là luận điểm nên đưa thẳng vào phần Security Implications
(5.2)/RQ3: hiệu quả cao hiện tại một phần phản ánh cách dataset vận hành hoá
kịch bản "clone", không nên khái quát hoá thành "đã giải quyết được bài toán
clone detection nói chung".

## Tái lập

```bash
python scripts/feature_importance.py --features features_all.csv --splits splits.csv \
    --out-dir results_4_5/
```

Ra 2 file CSV bảng đầy đủ + 1 file PNG (`shap_importance_E3.png`) dùng minh
hoạ trong bài (không phải trọng tâm — trọng tâm là bảng + phần diễn giải phía
trên).
