"""
Section 3.2/3.3 support script for RFID-ExSim.

Turns raw per-event JSONL (S1/S2/S3) into one row per session_id with:
  - behavioral evidence features (temporal, reader-transition, physical consistency)
  - protocol evidence features (cross-reader UID duplication signal, standing in
    for the Modified BASE / Modified Count-Min counters described in 2.2/3.3 --
    replace PROTOCOL_WINDOW_S / the exact-count logic with your own MB/MCM
    implementation once it exists; keep the column names so 3.4 keeps working)
  - label: 0 = genuine (S1 baseline, S2 legitimate dual-reader), 1 = cloned-proxy
    (S3: same UID read by two different readers within a short delta -> the
    "Same UID + Different Reader/Location/Time" signal from the proposal)
  - group_key = tag_local_id, so 3.5's group-aware split can keep every read of
    a physical tag on one side of the train/val/test boundary

Usage:
    python build_features.py --data-dir /path/to/rfid_dataset --out features_all.csv
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

BEHAVIORAL_COLS = [
    "n_reads", "success_rate", "duration_s",
    "mean_inter_read_ms", "std_inter_read_ms", "max_inter_read_ms",
    "n_distinct_readers", "reader_transition_count", "reader_transition_rate",
    "n_distinct_distance", "distance_std",
    "n_distinct_orientation", "orientation_std",
    "impossible_movement_count", "impossible_movement_rate",
]

PROTOCOL_COLS = [
    "mb_duplicate_flag", "mb_concurrent_reader_max",
    "mb_min_cross_reader_delta_ms",
    "mcm_read_count_window", "mcm_suspicion_score",
]

META_COLS = ["session_id", "scenario", "tag_local_id", "group_key", "label"]

# a genuine tag cannot plausibly move/re-orient between two reads a few ms apart
IMPOSSIBLE_DT_MS = 30.0
# window used for the protocol-evidence proxy (MB: near-simultaneous cross-reader
# duplicate; MCM: read-count within a slightly longer window)
MB_WINDOW_S = 0.05
MCM_WINDOW_S = 2.0


def load_scenario(data_dir: Path, scenario: str) -> pd.DataFrame:
    path = data_dir / "data" / "processed" / f"rfid_dataset_{scenario}_all.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    df = pd.DataFrame(rows)
    df["timestamp_iso"] = pd.to_datetime(df["timestamp_iso"], utc=True)

    # QC step from methodology.md section 4: some S1 raw logs contain ESP32
    # boot/serial noise lines (event == "raw", no tag_local_id/uid_hash) --
    # these are not read events and must be dropped before feature extraction
    n_before = len(df)
    df = df[df["event"] == "read_success"].dropna(subset=["tag_local_id", "uid_hash"])
    dropped = n_before - len(df)
    if dropped:
        print(f"[QC] {scenario}: dropped {dropped}/{n_before} non-read/malformed events")
    return df.reset_index(drop=True)


def add_protocol_evidence(df: pd.DataFrame) -> pd.DataFrame:
    """Per-event cross-reader duplication signal, computed on the *global*
    timeline (protocol verification sees the live stream, not one session)."""
    df = df.sort_values("timestamp_iso").reset_index(drop=True)
    ts = df["timestamp_iso"].values.astype("datetime64[ns]").astype(np.int64) / 1e9
    uid = df["uid_hash"].values
    dev = df["device_id"].values

    n = len(df)
    mb_flag = np.zeros(n, dtype=int)
    mb_min_delta = np.full(n, np.nan)
    mb_max_readers = np.ones(n, dtype=int)
    mcm_count = np.zeros(n, dtype=int)

    # group indices by uid_hash for O(events-per-uid) window scans
    by_uid = pd.Series(np.arange(n)).groupby(uid).apply(list).to_dict()
    for u, idxs in by_uid.items():
        idxs = np.array(idxs)
        u_ts = ts[idxs]
        u_dev = dev[idxs]
        order = np.argsort(u_ts)
        idxs, u_ts, u_dev = idxs[order], u_ts[order], u_dev[order]
        for i in range(len(idxs)):
            lo_mb = np.searchsorted(u_ts, u_ts[i] - MB_WINDOW_S, side="left")
            hi_mb = np.searchsorted(u_ts, u_ts[i] + MB_WINDOW_S, side="right")
            window_devs = u_dev[lo_mb:hi_mb]
            other = window_devs[window_devs != u_dev[i]]
            mb_max_readers[idxs[i]] = len(set(window_devs))
            if len(other) > 0:
                mb_flag[idxs[i]] = 1
                deltas = np.abs(u_ts[lo_mb:hi_mb][window_devs != u_dev[i]] - u_ts[i]) * 1000.0
                mb_min_delta[idxs[i]] = deltas.min()

            lo_m = np.searchsorted(u_ts, u_ts[i] - MCM_WINDOW_S, side="left")
            hi_m = np.searchsorted(u_ts, u_ts[i] + MCM_WINDOW_S, side="right")
            mcm_count[idxs[i]] = hi_m - lo_m

    df["mb_duplicate_flag"] = mb_flag
    df["mb_min_cross_reader_delta_ms"] = mb_min_delta
    df["mb_concurrent_reader_max"] = mb_max_readers
    df["mcm_read_count_window"] = mcm_count
    # suspicion score: normalised read pressure within the window (MCM-style signal)
    df["mcm_suspicion_score"] = df["mcm_read_count_window"] / (2 * MCM_WINDOW_S)
    return df


def session_features(df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    rows = []
    for session_id, g in df.groupby("session_id"):
        g = g.sort_values("timestamp_iso")
        ts = g["timestamp_iso"].astype(np.int64) / 1e9
        dt_ms = ts.diff().dropna() * 1000.0
        dev = g["device_id"]
        transitions = (dev != dev.shift()).sum() - 1
        transitions = max(transitions, 0)

        impossible = 0
        if len(g) > 1:
            dist_diff = g["distance_cm"].diff().abs()
            orient_diff = g["orientation_deg"].diff().abs()
            fast = dt_ms.reindex(g.index[1:]).values < IMPOSSIBLE_DT_MS
            moved = (dist_diff.values[1:] > 0) | (orient_diff.values[1:] > 0)
            impossible = int(np.sum(fast & moved))

        n_reads = len(g)
        rows.append({
            "session_id": session_id,
            "scenario": scenario,
            "tag_local_id": g["tag_local_id"].iloc[0],
            "n_reads": n_reads,
            "success_rate": (g["event"] == "read_success").mean(),
            "duration_s": float(ts.iloc[-1] - ts.iloc[0]),
            "mean_inter_read_ms": float(dt_ms.mean()) if len(dt_ms) else 0.0,
            "std_inter_read_ms": float(dt_ms.std()) if len(dt_ms) > 1 else 0.0,
            "max_inter_read_ms": float(dt_ms.max()) if len(dt_ms) else 0.0,
            "n_distinct_readers": g["device_id"].nunique(),
            "reader_transition_count": int(transitions),
            "reader_transition_rate": transitions / max(n_reads - 1, 1),
            "n_distinct_distance": g["distance_cm"].nunique(),
            "distance_std": float(g["distance_cm"].std()) if n_reads > 1 else 0.0,
            "n_distinct_orientation": g["orientation_deg"].nunique(),
            "orientation_std": float(g["orientation_deg"].std()) if n_reads > 1 else 0.0,
            "impossible_movement_count": impossible,
            "impossible_movement_rate": impossible / max(n_reads - 1, 1),
            "mb_duplicate_flag": g["mb_duplicate_flag"].max(),
            "mb_concurrent_reader_max": g["mb_concurrent_reader_max"].max(),
            "mb_min_cross_reader_delta_ms": g["mb_min_cross_reader_delta_ms"].min(),
            "mcm_read_count_window": g["mcm_read_count_window"].mean(),
            "mcm_suspicion_score": g["mcm_suspicion_score"].mean(),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True, help="path to .../rfid_dataset")
    ap.add_argument("--out", default="features_all.csv")
    args = ap.parse_args()
    data_dir = Path(args.data_dir)

    frames = []
    for scenario, label in [("S1", 0), ("S2", 0), ("S3", 1)]:
        raw = load_scenario(data_dir, scenario)
        raw = add_protocol_evidence(raw)
        feats = session_features(raw, scenario)
        feats["label"] = label
        frames.append(feats)

    out = pd.concat(frames, ignore_index=True)
    out["mb_min_cross_reader_delta_ms"] = out["mb_min_cross_reader_delta_ms"].fillna(
        out["mb_min_cross_reader_delta_ms"].max() if out["mb_min_cross_reader_delta_ms"].notna().any() else 0.0
    )
    out["group_key"] = out["tag_local_id"]
    out = out[META_COLS + BEHAVIORAL_COLS + PROTOCOL_COLS]

    out.to_csv(args.out, index=False)
    print(f"wrote {len(out)} session-level rows -> {args.out}")
    print(out["label"].value_counts().rename({0: "genuine", 1: "cloned-proxy"}))
    print(out.groupby("scenario").size())


if __name__ == "__main__":
    main()
