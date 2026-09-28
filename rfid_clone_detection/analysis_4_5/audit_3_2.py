"""Section 3.2 data audit: raw events -> quality checks -> session-level samples."""
import json
import os
import re
import numpy as np
import pandas as pd

ROOT = os.environ.get("RFID_DATA", "rfid_dataset")
PROC = os.path.join(ROOT, "data", "processed")
FIELDS = ["timestamp_iso", "session_id", "scenario", "device_id", "tag_local_id", "uid_hash",
          "uid_plain_local", "distance_cm", "orientation_deg", "event", "raw_payload"]


def load(s):
    rows = [json.loads(l) for l in open(os.path.join(PROC, f"rfid_dataset_{s}_all.jsonl")) if l.strip()]
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["timestamp_iso"], utc=True, format="mixed")
    return df


def nun(d, c):
    return d[c].nunique() if c in d else np.nan


pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
audit, raw = [], {}
for s in ["S1", "S2", "S3", "S4", "S5"]:
    df = load(s); raw[s] = df
    ok = df[df["event"] == "read_success"]
    dup_exact = df.drop(columns=["ts"]).astype(str).duplicated().sum()
    dup_key = ok.duplicated(subset=["session_id", "device_id", "timestamp_iso"]).sum()
    audit.append(dict(
        scenario=s, events=len(df), read_success=len(ok), non_read=len(df) - len(ok),
        event_types=dict(df["event"].value_counts()), sessions=df["session_id"].nunique(),
        readers=nun(ok, "device_id"), tags=nun(ok, "tag_local_id"),
        uids_plain=nun(ok, "uid_plain_local"), uid_hashes=nun(ok, "uid_hash"),
        t_min=ok["ts"].min(), t_max=ok["ts"].max(),
        dup_exact=int(dup_exact), dup_same_reader_timestamp=int(dup_key),
        missing={c: int(df[c].isna().sum()) for c in FIELDS if c in df and df[c].isna().any()},
        absent_fields=[c for c in FIELDS if c not in df]))
A = pd.DataFrame(audit)
print(A.drop(columns=["event_types", "missing", "absent_fields"]).to_string(index=False))
print()
for r in audit:
    print(r["scenario"], "| event types:", r["event_types"], "| missing:", r["missing"], "| absent:", r["absent_fields"])

print("\n=== total events all scenarios:", int(A.events.sum()), "| S1-S3:", int(A.events[:3].sum()),
      "| S1-S3 read_success:", int(A.read_success[:3].sum()))

# UID consistency across scenarios
ok_all = pd.concat([raw[s][raw[s].event == "read_success"].assign(sc=s) for s in ["S1", "S2", "S3"]])
m = ok_all.groupby("tag_local_id").agg(uid_plain=("uid_plain_local", "nunique"), uid_hash=("uid_hash", "nunique"))
print("\nper tag across S1-S3: uid_plain values", m.uid_plain.unique(), "| uid_hash values", m.uid_hash.unique())
print("uid_hash == lower(uid_plain) share by scenario:",
      ok_all.assign(eq=ok_all.uid_hash == ok_all.uid_plain_local.str.lower()).groupby("sc").eq.mean().round(3).to_dict())

# session durations and events/session (read_success)
for s in ["S1", "S2", "S3"]:
    ok = raw[s][raw[s].event == "read_success"]
    g = ok.groupby("session_id")
    d = (g.ts.max() - g.ts.min()).dt.total_seconds()
    print(f"{s}: reads/session min/med/max {g.size().min()}/{g.size().median():.0f}/{g.size().max()} | "
          f"duration s min/med/max {d.min():.1f}/{d.median():.1f}/{d.max():.1f} | "
          f"reads per reader {ok.device_id.value_counts().to_dict()}")

# class balance at each level
s1m = pd.read_csv(os.path.join(PROC, "meta_sessions_S1.csv"))
s2c = pd.read_csv(os.path.join(PROC, "s2_collisions_summary.csv"))
s3c = pd.read_csv(os.path.join(PROC, "s3_clone_collisions_summary.csv"))
gen_ev = int(A.read_success[0] + A.read_success[1]); clo_ev = int(A.read_success[2])
print(f"\nevent level (read_success): genuine S1+S2={gen_ev} clone S3={clo_ev} ratio={gen_ev/clo_ev:.2f}:1")
print(f"summary-file level: S1 meta sessions={len(s1m)} | S2 collision pairs={len(s2c)} | S3 collision pairs={len(s3c)}")
print("summary files missing:", {n: int(d.isna().sum().sum()) for n, d in [('S1', s1m), ('S2', s2c), ('S3', s3c)]},
      "| duplicate rows:", {n: int(d.duplicated().sum()) for n, d in [('S1', s1m), ('S2', s2c), ('S3', s3c)]})
print("sessions: S1", s1m.session_id.nunique(), "S2", s2c.session_id.nunique(), "S3", s3c.session_id.nunique())
print("S1 planned repetitions:", s1m.repetitions.value_counts().to_dict(), "| total_reads min/max", s1m.total_reads.min(), s1m.total_reads.max())
print("S3 pairs/session min/med/max", s3c.groupby('session_id').size().agg(['min', 'median', 'max']).tolist())
print("S2 pairs/session min/med/max", s2c.groupby('session_id').size().agg(['min', 'median', 'max']).tolist())
print("S1 sessions per tag:", s1m.groupby('tag_local_id').size().unique(), "| distances", sorted(s1m.distance_cm.unique()),
      "| orientations", sorted(s1m.orientation_deg.unique()))
print("S2 sessions per tag:", s2c.groupby(s2c.session_id.str.extract(r'(TAG\d+)')[0]).session_id.nunique().unique())
