import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from replicate_team import (evidence_data, E3, PROTOCOL_FEATURES, s1, s2_coll, s3)

ed = evidence_data
print("=" * 80, "\n[A] Per-feature class separation (full 216 rows)\n")
rows = []
for c in E3:
    r, k = ed.loc[ed.label == 0, c], ed.loc[ed.label == 1, c]
    auc = roc_auc_score(ed.label, ed[c].fillna(ed[c].median()))
    auc = max(auc, 1 - auc)
    overlap = not (r.max() < k.min() or k.max() < r.min())
    rows.append(dict(feature=c, real_min=r.min(), real_med=r.median(), real_max=r.max(),
                     clone_min=k.min(), clone_med=k.median(), clone_max=k.max(),
                     single_feature_AUC=auc, ranges_overlap=overlap))
t = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
print(t.round(4).to_string(index=False))
print("\nfeatures that ALONE separate classes perfectly (AUC=1, no overlap):",
      (~t.ranges_overlap).sum(), "/", len(t))

print("\n" + "=" * 80, "\n[B] Provenance audit\n")
print("S2 dt: signed?", (s2_coll.dt < 0).mean().round(3), "negative share | max|dt| (s):",
      s2_coll.dt.abs().max().round(4), "| median |dt| (s):", s2_coll.dt.abs().median().round(4))
print("S3 delta_ms: any negative?", (s3.delta_ms < 0).any(), "| max (ms):", s3.delta_ms.max())
tA = pd.to_datetime(s3.t_reader_A); tB = pd.to_datetime(s3.t_reader_B)
signed = (tB - tA).dt.total_seconds() * 1000
print("S3 signed (tB-tA) negative share:", (signed < 0).mean().round(3),
      "| delta_ms == |tB-tA| exactly:", np.allclose(s3.delta_ms, signed.abs(), atol=1e-6))
frac_int = (np.abs(s3.delta_ms - s3.delta_ms.round()) < 0.0015).mean()
print("S3 delta_ms on ~integer-ms grid:", round(frac_int, 3),
      "| S2 dt exactly zero share:", (s2_coll.dt == 0).mean())
print("S2 |dt|<=5ms share of pairs:", (s2_coll.dt.abs() <= 0.005).mean().round(4))
print("\nread_count definitions:")
print("  Real (S1 total_reads): min/med/max", s1.total_reads.min(), s1.total_reads.median(), s1.total_reads.max(),
      "| planned repetitions:", sorted(s1.repetitions.unique()))
s3c = s3.groupby("session_id").size()
print("  Clone (S3 #collision pairs): min/med/max", s3c.min(), s3c.median(), s3c.max())

print("\n" + "=" * 80, "\n[C] Grouping & pairing audit\n")
print("groups per class:", ed.groupby("label").tag_group.nunique().to_dict())
print("example clone tag_group values:", ed[ed.label == 1].tag_group.head(3).tolist())
real = ed[ed.label == 0]
print("real rows whose protocol session (S2) and behavior session (S1) are the SAME experiment:",
      (real.session_id.str.extract(r"_(S\d)_")[0] == real.behavior_session_id.str.extract(r"_(S\d)_")[0]).sum(),
      "/", len(real))
print("example real pairing:", real[["session_id", "behavior_session_id"]].iloc[0].tolist())
