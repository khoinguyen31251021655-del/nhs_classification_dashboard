# Chạy 3.4 + 3.5 bằng terminal / PyCharm (PySpark local)

Dùng khi cần debug từng bước (đặt breakpoint trong PyCharm), hoặc khi Colab
disconnect làm khó chạy nhiều seeds liên tục.

## 1. Yêu cầu hệ thống

- Python 3.10/3.11
- Java 11 hoặc 17 (Spark 3.5 cần JDK; kiểm tra bằng `java -version`)
- Không cần cài Hadoop/Spark cluster riêng — `pip install pyspark` đã kèm
  sẵn Spark chạy chế độ local (`local[*]`)

## 2. Tạo project trong PyCharm

1. New Project → chọn interpreter Python 3.11, tick "New virtualenv".
2. Copy toàn bộ thư mục `rfid_clone_detection/` (script + docs) vào project,
   và giải nén `RFID-ExSim-dataset.zip` vào một thư mục bên cạnh, ví dụ
   `data/RFID-ExSim-dataset/`.
3. Terminal trong PyCharm (Alt+F12):

```bash
pip install -r rfid_clone_detection/requirements.txt
```

Nếu máy dùng Debian/Ubuntu và gặp lỗi build wheel kiểu
`AttributeError: install_layout` khi cài `pyspark` — đó là xung đột giữa
`setuptools` hệ thống (bản Debian có patch `--install-layout=deb`) với gói
`pyspark`. Cách né nhanh nhất: tạo virtualenv sạch rồi cài trong đó thay vì
dùng `pip` hệ thống:

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r rfid_clone_detection/requirements.txt
```

## 3. Chạy pipeline (3 lệnh, đúng thứ tự)

```bash
cd rfid_clone_detection

python scripts/build_features.py \
    --data-dir /path/to/RFID-ExSim-dataset/rfid_dataset/rfid_dataset \
    --out features_all.csv

python scripts/split_leakage_safe.py \
    --features features_all.csv --out splits.csv --seed 42 --n-folds 5

python scripts/train_detectors.py \
    --features features_all.csv --splits splits.csv \
    --out results_3_4.csv --seeds 42,7,123,2024,99 --n-folds 5
```

Trong PyCharm có thể tạo 3 **Run Configuration** (Script path + Parameters)
tương ứng 3 lệnh trên để bấm chạy/debug từng bước mà không gõ lại terminal.

## 4. Debug gợi ý

- Đặt breakpoint trong `build_features.py::add_protocol_evidence` nếu nghi
  ngờ cửa sổ MB/MCM (`MB_WINDOW_S`, `MCM_WINDOW_S`) chưa khớp với thiết kế
  ở 3.3 của nhóm — đây là hai hằng số **cần nhóm tự tinh chỉnh/thay bằng
  MB/MCM thật** đã cài ở 2.2, script hiện chỉ dùng một proxy đơn giản.
- `train_detectors.py` in ra từng dòng kết quả (`print(row)`) ngay khi chạy
  xong mỗi `(config, model, seed)` — theo dõi log này để biết đang ở seed
  nào nếu chạy lâu (5 seeds × 2 model × 2 config ~ 20 lần fit CrossValidator).
- Spark UI (mặc định `http://localhost:4040` khi script đang chạy) cho xem
  từng stage/job nếu cần kiểm tra tại sao một fold chạy chậm.

## 5. Sau khi chạy xong

`results_3_4_summary.csv` là bảng mean±SD dùng trực tiếp cho báo cáo (4.2,
4.3). Giữ lại `splits.csv` — đây chính là bằng chứng tái lập được cho phần
3.5 (Thầy có thể hỏi lại cách chia tập, chỉ cần trỏ vào file này + assertion
trong `split_leakage_safe.py`).
