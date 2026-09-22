# Kết quả chạy thử thật (1 seed, smoke test) trên RFID-ExSim

Toàn bộ pipeline (`build_features.py` → `split_leakage_safe.py` →
`train_detectors.py`) đã chạy thành công end-to-end bằng PySpark thật (Spark
3.5.1, local mode) trên chính `RFID-ExSim-dataset.zip`. Kết quả 1 seed dưới
đây **không phải** con số cuối để đưa vào bài báo (bài báo cần 5 seeds theo
4.1) — mục đích là xác nhận code chạy đúng và cho thấy một phát hiện quan
trọng nhóm nên bàn ở 4.3/4.4.

| config | model | accuracy | recall_cloned | fpr | fnr |
|---|---|---|---|---|---|
| E1 – Protocol Only (rule MB/MCM) | — | 0.667 | 1.000 | **0.500** | 0.000 |
| E2 – Behavioral Only | Random Forest | 1.000 | 1.000 | 0.000 | 0.000 |
| E2 – Behavioral Only | SVM | 1.000 | 1.000 | 0.000 | 0.000 |
| E3 – Combined | Random Forest | 1.000 | 1.000 | 0.000 | 0.000 |
| E3 – Combined | SVM | 1.000 | 1.000 | 0.000 | 0.000 |

## Phát hiện 1 — đúng như dự đoán ở `leakage_evidence.md`

E1 (protocol-only) bắt được **100% clone** (recall=1.0) nhưng **báo động giả
trên 50% thẻ genuine** (fpr=0.5) — vì `mb_duplicate_flag` kích hoạt bất cứ
khi nào có ≥2 reader đọc cùng UID gần như đồng thời, và điều đó đúng với
**cả S2 (hợp lệ) lẫn S3 (cloned-proxy)**. Đây là bằng chứng số liệu trực
tiếp cho RQ2/4.3: protocol evidence một mình không đủ để phân biệt "2 reader
đọc hợp lệ" với "clone", và cho đúng câu chuyện Thầy muốn: *"phân tích tại
sao protocol evidence có thể redundant hoặc làm tăng false alarm"*.

## Phát hiện 2 — CẢNH BÁO quan trọng, cần đưa vào Limitations (5.3)

E2/E3 đạt **accuracy/recall/precision = 1.000 tuyệt đối** với cả RF lẫn SVM.
Điều này **không có nghĩa bài toán đã "giải xong"** — nó phản ánh cách dataset
được dựng: S3 (cloned-proxy) có `mcm_read_count_window` trung bình ≈1500
trong khi S1/S2 (genuine) chỉ ≈2.5–61.5 (xem `leakage_evidence.md`), tức là
mật độ đọc giữa 2 lớp lệch nhau ~25–600 lần — một khoảng cách quá lớn so với
kịch bản tấn công thực tế (attacker giỏi sẽ cố mô phỏng hành vi đọc bình
thường). Với chỉ 12 group (tag) và ranh giới lớp rõ như vậy, RF/SVM tách
tuyệt đối là dễ hiểu, nhưng:

- **Không nên báo cáo "accuracy 100%" như một thành tựu** trong bài — reviewer
  sẽ nghi ngờ ngay. Nên diễn giải: kết quả cho thấy trên **kịch bản clone rõ
  ràng** (2 reader đọc dồn dập gần như liên tục) detector tách hoàn hảo, và
  nêu rõ đây là giới hạn của dataset (12 tag, môi trường kiểm soát, S3 dùng
  tốc độ đọc rất cao — gần với hành vi "flooding" hơn là một attacker tinh vi
  cố giấu dấu vết).
- **Đề xuất cải thiện trước khi lấy số final**: (1) chạy 5 seeds như yêu cầu
  và báo mean±SD dù có thể vẫn ~1.0 — SD=0 cũng là một con số cần nói rõ
  trong bài, không nên giấu; (2) cân nhắc dựng thêm một biến thể "clone tinh
  vi" (vd. hạ tốc độ đọc của S3 xuống gần S2 để kiểm tra detector còn phân
  biệt được không) nếu còn thời gian — đây sẽ là thí nghiệm rất mạnh cho
  phần 4.4 Security Failure Analysis (False Negative case study); (3) nếu
  không kịp làm thêm, vẫn có thể dùng nguyên kết quả này nhưng phải viết rõ
  trong Limitations rằng phân biệt genuine/cloned trong dataset hiện tại dựa
  chủ yếu vào chênh lệch tốc độ đọc rất lớn giữa 2 scenario.

## Cách tái lập

```bash
python scripts/build_features.py --data-dir /path/to/rfid_dataset --out features_all.csv
python scripts/split_leakage_safe.py --features features_all.csv --out splits.csv --seed 42 --n-folds 5
python scripts/train_detectors.py --features features_all.csv --splits splits.csv \
    --out results_3_4.csv --seeds 42,7,123,2024,99 --n-folds 5
```
