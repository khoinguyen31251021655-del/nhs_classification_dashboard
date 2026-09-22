# 3.4 Detection Configurations & 3.5 Leakage-Safe Evaluation Protocol

Bộ code + hướng dẫn này đã được test trực tiếp trên `RFID-ExSim-dataset.zip`
nhóm gửi (12 tag, 2 reader ESP32-MFRC522, scenario S1–S5) và trên nội dung
góp ý của Thầy trong file `ANTT — NỘI DUNG CẦN LÀM`. Mục tiêu: làm đúng
3.4/3.5 với dữ liệu thật, không phải pseudo-code.

## 0. Ánh xạ scenario → nhãn genuine/cloned (quyết định cần ghi rõ ở 3.2)

Dataset **không có** hai thẻ vật lý khác nhau cùng UID thật (xem
`data/plans/s3_plan.csv`: cột `uid_original` và `uid_clone` luôn bằng nhau —
nhóm mô phỏng "cloned tag" bằng cách cho **cùng một UID bị đọc bởi 2 reader
gần như đồng thời**, đúng với mô tả `docs/scenarios.md` S3: *"Tag Duplication
/ UID Equivalence"* và đúng với Problem Statement 1.2 của Thầy: *"Same UID +
Different Reader/Location/Time → Suspicious Behavior"*).

Vì vậy, script `build_features.py` gán:

| Scenario | Ý nghĩa | Nhãn |
|---|---|---|
| S1 — baseline, 1 reader | Genuine, không có gì bất thường | `0` genuine |
| S2 — 2 reader đọc **hợp lệ** cùng lúc (overlap vùng phủ sóng) | Genuine nhưng "trông giống" clone (hard negative) | `0` genuine |
| S3 — cùng UID xuất hiện ở 2 reader gần như đồng thời | Cloned-proxy | `1` cloned |

**Đưa S2 vào làm hard-negative là điểm nên nêu rõ trong 3.2/4.4** — nó chứng
minh detector không chỉ "thấy 2 reader là báo động", mà phải phân biệt được
đọc-2-reader-hợp-lệ với đọc-2-reader-do-bị-nhân-bản. Chi tiết + số liệu cụ
thể chứng minh protocol-only sẽ nhầm S2 với S3: `docs/leakage_evidence.md`.

S4 (replay) và S5 (flooding) **không** dùng cho 3.4/3.5 — đúng theo giới hạn
Thầy đặt ở 5.3 ("chưa đánh giá replay/flooding") và đúng với phạm vi proposal
("tập trung vào baseline single-reader operation và UID-level tag cloning").

## 1. Thứ tự chạy (3.2 → 3.3 → 3.4 → 3.5 đã gộp thành 3 script)

```
scripts/build_features.py       # 3.2 QC + 3.3 feature engineering (behavioral + protocol proxy)
        │  -> features_all.csv  (324 dòng session-level: 216 genuine / 108 cloned-proxy)
        ▼
scripts/split_leakage_safe.py   # 3.5 group-aware Train/Val/Test + group-aware CV folds
        │  -> splits.csv
        ▼
scripts/train_detectors.py      # 3.4 ablation E1/E2/E3 × (RF, SVM), PySpark, multi-seed
        │  -> results_3_4.csv, results_3_4_summary.csv
```

Chạy trên Colab: `docs/colab_quickstart.md`.
Chạy local/PyCharm: `docs/pycharm_local_setup.md`.

## 2. 3.3 recap — 2 nhóm đặc trưng (để 3.4 ablation có ý nghĩa)

`build_features.py` xuất đúng 2 nhóm cột theo yêu cầu 3.3 của Thầy:

**A. Behavioral evidence** (`BEHAVIORAL_COLS`): read frequency (`n_reads`,
`success_rate`), inter-read time (`mean/std/max_inter_read_ms`), reader
transition (`n_distinct_readers`, `reader_transition_count/rate`), distance/
orientation variation (`*_std`), và `impossible_movement_count/rate` — số
lần khoảng cách/góc đổi trong <30ms giữa 2 lần đọc liên tiếp (một tag vật lý
không thể di chuyển/đổi hướng trong thời gian đó → dấu hiệu bất thường vật
lý, đúng tinh thần "Impossible Movement Indicator" Thầy liệt kê).

**B. Protocol evidence** (`PROTOCOL_COLS`): đây là **proxy đơn giản** đứng
thay cho MB (Modified BASE) / MCM (Modified Count-Min) thật mà nhóm cần cài
ở 2.2/3.3 — `mb_duplicate_flag`/`mb_concurrent_reader_max`/
`mb_min_cross_reader_delta_ms` mô phỏng tín hiệu MB (UID bị đọc bởi >1 reader
trong cửa sổ 50ms), `mcm_read_count_window`/`mcm_suspicion_score` mô phỏng
MCM (mật độ đọc UID trong cửa sổ 2s — CMS thật dùng xấp xỉ để tiết kiệm bộ
nhớ ở scale lớn, ở đây dataset nhỏ nên đếm chính xác đóng vai trò tương
đương). **Khi nhóm đã code xong MB/MCM thật ở 2.2, chỉ cần thay phần thân
hàm `add_protocol_evidence()` — giữ nguyên tên 5 cột này thì `train_detectors.py`
không cần sửa gì.**

Mỗi dòng dữ liệu = 1 `session_id` (ứng với 1 lần trình bày tag ở 1
distance×orientation×run) → đây chính là "aggregation/window rule" nhóm
phải ghi rõ ở 3.2 (Thầy nhắc: "không chỉ nói tag-level aggregation").

## 3. 3.4 — Detection Configurations, đúng thiết kế Thầy yêu cầu

```
E1 – Protocol Only        -> rule-based trên PROTOCOL_COLS (KHÔNG train RF/SVM)
E2 – Behavioral Only      -> Random Forest + SVM (LinearSVC) trên BEHAVIORAL_COLS
E3 – Protocol + Behavioral-> Random Forest + SVM (LinearSVC) trên cả 2 nhóm
```

Lý do E1 không chạy RF/SVM: đúng câu Thầy viết — *"Sau đó với E2/E3 chạy:
Random Forest và SVM"* — E1 đại diện cho khả năng phát hiện **của riêng
protocol** (ngưỡng cảnh báo MB/MCM), dùng làm baseline để trả lời RQ2
("Protocol+Behavioral có tốt hơn dùng riêng lẻ không?") và RQ3 (so sánh chi
phí tính toán). Ngưỡng của rule E1 được chọn trên **tập validation** (không
đụng tập test), y hệt cách chọn hyperparameter của RF/SVM — để so sánh 3
config công bằng.

RF dùng `pyspark.ml.classification.RandomForestClassifier`, SVM dùng
`LinearSVC` (SVM tuyến tính — Spark ML chưa có kernel phi tuyến; nếu muốn
kernel RBF phải dùng `sklearn.svm.SVC`, script kèm ghi chú cách đổi trong
`docs/pycharm_local_setup.md` nếu nhóm muốn thử offline). Cả hai đều chạy
qua `Pipeline([VectorAssembler, StandardScaler, classifier])` — chuẩn hoá
đặc trưng là bắt buộc với SVM vì các cột behavioral (vd. `n_reads` ~100-300)
và protocol (vd. `mcm_read_count_window` ~1-1500) khác biên độ rất lớn.

Hyperparameter tuning: `CrossValidator(..., foldCol="cv_fold")` — dùng đúng
cột fold **group-aware** do `split_leakage_safe.py` sinh ra, không phải
k-fold ngẫu nhiên của Spark mặc định.

Chạy lặp lại 5 seeds (`42,7,123,2024,99`, đổi được bằng `--seeds`) — đáp ứng
yêu cầu 4.1 ("tối thiểu 3 seeds, tốt hơn 5 seeds, báo mean ± SD"). Kết quả
mỗi seed = 1 dòng `results_3_4.csv`; bảng tổng hợp `results_3_4_summary.csv`
gộp theo `(config, model)`.

Metric ưu tiên đúng lưu ý 4.2: **không lấy Accuracy làm trọng tâm**, script
tính đủ `recall_cloned` (Cloned Recall), `fpr` (báo động giả trên thẻ thật),
`fnr` (bỏ sót clone), cộng `f1_cloned`/`precision_cloned`/`accuracy` để đối
chiếu.

## 4. 3.5 — Leakage-Safe Evaluation Protocol

Quyết định (thay cho việc "vừa 80/20 vừa 5-fold CV vừa session-aware" đang
mâu thuẫn trong proposal — Thầy yêu cầu nhóm chốt lại một phương án):

1. **Group-aware Train/Val/Test = 60/20/20**, group theo `tag_local_id`
   (tương đương UID, vì mỗi UID gắn cố định 1 tag suốt dataset). Dùng
   `sklearn.model_selection.GroupShuffleSplit` 2 bước (cắt test trước, rồi
   cắt val từ phần còn lại) — **không** dùng train_test_split ngẫu nhiên.
2. **Group-aware K-fold CV (k=5) chỉ trên phần Train**, cũng group theo
   `tag_local_id`, dùng để chọn hyperparameter RF/SVM (không đụng vào Val/
   Test). Đây là thứ tự Thầy yêu cầu: *"Ưu tiên Session-aware Split, sau đó
   mới Group-aware CV on Training Set."*
3. Không dùng random event-level split ở bất kỳ bước nào.

Script tự kiểm chứng bằng `assert_no_group_leakage()`: nếu bất kỳ
`tag_local_id` nào lọt sang >1 phía train/val/test, script crash ngay thay
vì âm thầm sinh kết quả sai — nên đưa dòng assertion này vào phụ lục
báo cáo (evidence tái lập được cho 3.5).

Vì dataset thật chỉ có **12 group** (12 tag), số lượng nhóm khá ít — chạy
nhiều seed cho bước split (không chỉ cho RF/SVM) cũng nên làm nếu nhóm muốn
báo cáo độ nhạy của kết quả với cách chia (tham số `--seed` của
`split_leakage_safe.py`).

## 5. Điều nhóm KHÔNG nên báo cáo (theo đúng cảnh báo trong file góp ý)

- Không claim "real-time" chỉ vì `inference_ms_per_sample` thấp trên Colab —
  script đo **batch-transform latency trên CPU Colab**, không phải độ trễ
  triển khai thật trên ESP32/checkpoint. Diễn đạt đúng tinh thần 4.6: nói
  "computational feasibility for checkpoint-oriented deployment".
- Không kết luận "RF tốt hơn SVM" là câu hỏi khoa học chính — câu hỏi chính
  là **nguồn evidence nào (E1/E2/E3) giúp phát hiện clone**, RF/SVM chỉ là
  công cụ đo trên E2/E3.
- Nếu Combined (E3) không thắng rõ Behavioral (E2), đừng cố ép số — phân
  tích tại sao protocol evidence có thể redundant/tăng false alarm (xem
  bằng chứng cụ thể về S2 vs S3 ở `docs/leakage_evidence.md`, phần
  `mb_duplicate_flag` không phân biệt được 2 scenario này).

## 6. File trong thư mục này

```
rfid_clone_detection/
├── README.md                        # file này
├── requirements.txt
├── scripts/
│   ├── build_features.py            # 3.2 QC + 3.3 feature engineering
│   ├── split_leakage_safe.py        # 3.5 group-aware split + CV folds
│   └── train_detectors.py           # 3.4 E1/E2/E3 × RF/SVM (PySpark), multi-seed
└── docs/
    ├── colab_quickstart.md          # copy-paste cell cho Google Colab
    ├── pycharm_local_setup.md       # chạy bằng terminal / PyCharm local
    └── leakage_evidence.md          # bằng chứng số liệu thật cho 3.5 + insight S2 vs S3
```

Toàn bộ đã chạy thử thành công trên chính `RFID-ExSim-dataset.zip` nhóm gửi
(pandas/scikit-learn phần feature+split; phần PySpark `train_detectors.py`
đã review kỹ theo API `pyspark.ml`/`CrossValidator(foldCol=...)` — nhớ chạy
thử 1 lượt trên Colab trước khi lấy số final, vì môi trường sandbox này
không cài được PySpark do lỗi packaging cục bộ không liên quan tới Colab).
