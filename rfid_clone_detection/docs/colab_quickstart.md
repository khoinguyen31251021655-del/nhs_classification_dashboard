# Chạy 3.4 + 3.5 trên Google Colab

## Cell 1 — cài đặt (chỉ mất ~1 phút, không cần GPU)

```python
!pip install -q pyspark==3.5.1 scikit-learn pandas
```

Colab đã có sẵn Java, `pyspark` cài bằng pip là chạy được ngay (không cần
tự cài Spark cluster).

## Cell 2 — lấy dataset

Cách gọn nhất: upload `RFID-ExSim-dataset.zip` lên Google Drive, mount Drive,
rồi giải nén:

```python
from google.colab import drive
drive.mount('/content/drive')

!unzip -q "/content/drive/MyDrive/RFID-ExSim-dataset.zip" -d /content/rfid_raw
DATA_DIR = "/content/rfid_raw/RFID-ExSim-dataset/rfid_dataset/rfid_dataset"
```

(Sửa lại đường dẫn cho khớp với nơi bạn để file zip trong Drive.)

## Cell 3 — lấy code của nhóm

Nếu code (`build_features.py`, `split_leakage_safe.py`, `train_detectors.py`)
đã push lên GitHub cùng repo với bài báo:

```python
!git clone https://github.com/<owner>/<repo>.git /content/repo
SCRIPTS = "/content/repo/rfid_clone_detection/scripts"
```

Hoặc đơn giản hơn khi chỉ có 3 người chạy thử: dùng `%%writefile` để dán
thẳng nội dung 3 file `.py` vào 3 cell riêng trong Colab.

## Cell 4 — 3.2/3.3: xây feature table (genuine vs cloned-proxy)

```python
!python {SCRIPTS}/build_features.py --data-dir "{DATA_DIR}" --out /content/features_all.csv
```

In ra số dòng session-level, phân bố nhãn, và cảnh báo QC (vd: 532 sự kiện
"raw"/boot-log trong S1 bị loại — xem `docs/leakage_evidence.md` để hiểu vì
sao đây là bước QC bắt buộc trước khi gộp sample, đúng yêu cầu 3.2 của Thầy).

## Cell 5 — 3.5: leakage-safe split

```python
!python {SCRIPTS}/split_leakage_safe.py \
    --features /content/features_all.csv \
    --out /content/splits.csv --seed 42 --n-folds 5
```

Script tự `assert` không có `tag_local_id` nào lọt qua 2 phía train/val/test —
nếu bạn đổi `group_key` (vd. thử theo `session_id` thay vì `tag_local_id`) mà
assertion vẫn qua, tự kiểm tra lại xem có đúng ý đồ leakage-safe không.

## Cell 6 — 3.4: ablation E1/E2/E3 với RF & SVM (PySpark)

```python
!python {SCRIPTS}/train_detectors.py \
    --features /content/features_all.csv \
    --splits /content/splits.csv \
    --out /content/results_3_4.csv \
    --seeds 42,7,123,2024,99 \
    --n-folds 5
```

Chạy xong sẽ có 2 file:
- `results_3_4.csv` — từng lần chạy (mỗi seed × config × model một dòng)
- `results_3_4_summary.csv` — mean ± SD theo `(config, model)`, copy thẳng
  vào bảng 4.2 (E2, Behavioral Only) và bảng chính 4.3 (E1 vs E2 vs E3)

```python
import pandas as pd
pd.read_csv('/content/results_3_4_summary.csv')
```

## Lưu ý khi chạy trên Colab

- Runtime CPU thường (không cần GPU/TPU) là đủ — dataset sau khi gộp
  session-level chỉ còn vài trăm dòng, RF/SVM huấn luyện trong vài giây.
- Nếu Colab bị ngắt kết nối giữa chừng, chạy lại từ Cell 1 — không có state
  gì cần giữ giữa các cell ngoài 3 file CSV trung gian.
- Copy `results_3_4_summary.csv` và `splits.csv` về máy (hoặc lưu lại vào
  Drive) trước khi đóng phiên Colab, vì `/content` sẽ bị xoá.
