# Vì sao 80/20 random split KHÔNG dùng được trên RFID-ExSim

Chạy `build_features.py` trên dataset thật rồi kiểm tra chồng lấn group:

```python
df.groupby("tag_local_id")["label"].nunique().value_counts()
# label
# 2    12
```

Cả **12/12 thẻ vật lý** đều xuất hiện ở cả hai lớp (genuine từ S1/S2, cloned-proxy
từ S3) — vì thí nghiệm dùng đúng 12 tag cho mọi scenario. Hệ quả:

- Nếu split ngẫu nhiên theo `session_id` hoặc theo từng dòng sự kiện: gần như
  chắc chắn cùng một `tag_local_id`/`uid_hash` sẽ có mặt cả ở train và test.
- Model khi đó có thể học "UID = 3d9f24 → luôn là cloned" hay "UID = 83c1...
  → luôn là genuine" — tức là **học nhận diện danh tính thẻ**, không phải học
  **hành vi bất thường của việc bị nhân bản**. Đây chính xác là leakage mà
  Thầy cảnh báo trong 3.5: "Nếu cùng UID/session xuất hiện cả train và test
  thì model có thể 'nhớ' identity thay vì học cloning behavior."
- Ở dataset thật (checkpoint kho), detector phải tổng quát hoá sang **thẻ
  chưa từng thấy trong lúc train** — accuracy trên split rò rỉ sẽ lạc quan giả.

`split_leakage_safe.py` dùng `GroupShuffleSplit`/`GroupKFold` theo
`group_key = tag_local_id` để đảm bảo mỗi thẻ chỉ nằm ở đúng một trong
train/val/test, và assert việc này (`assert_no_group_leakage`) trước khi ghi
file ra — script sẽ crash ngay nếu vô tình có leakage, để không "âm thầm"
sinh ra một tập kết quả sai.

## Một phát hiện phụ đáng đưa vào 3.3/4.3

So sánh trung bình theo scenario (script `build_features.py`, cột
`mb_duplicate_flag` là tín hiệu MB-style "UID xuất hiện ở ≥2 reader gần như
đồng thời"):

| scenario | n_distinct_readers (mean) | mcm_read_count_window (mean) |
|---|---|---|
| S1 (genuine, 1 reader) | 1.56 | 2.5 |
| S2 (genuine, 2 reader hợp lệ) | 2.00 | 61.5 |
| S3 (cloned-proxy, 2 reader) | 2.00 | 1500.0 |

`mb_duplicate_flag` (chỉ nhìn "có ≥2 reader đọc cùng UID gần như đồng thời
không") **không phân biệt được S2 (hợp lệ) với S3 (cloned-proxy)** — cả hai
đều kích hoạt cờ này vì đúng là có 2 reader đọc cùng lúc. Đây là ví dụ cụ thể,
lấy từ chính dữ liệu, cho luận điểm ở 4.3: protocol evidence một mình có thể
gây false alarm trên tình huống hợp lệ (S2 = hai reader đọc chồng vùng phủ
sóng), và cần behavioral evidence (ở đây là `mcm_read_count_window`/tốc độ đọc
— S3 áp đảo S2 gần 25 lần) để tách hai trường hợp. Nên cân nhắc dùng S2 làm
**hard-negative** khi báo cáo False Positive ở 4.4, thay vì chỉ dùng S1.
