## 4.6. Detection Effectiveness vs Computational Overhead – RQ3

Table 7 compares E1 (MB/MCM), E2 (RF, SVM) and Hybrid E3 on detection, false alarms and computational cost. All methods reached Recall = 1.000 and FPR = 0.000 on every seed, so only cost separates them. Protocol extraction took 4.55 ms per session, while counting reads took under 0.001 ms. A decision took 0.11 ms with E1, 1.19 ms with SVM and 16.49 ms with RF. RF was also the slowest to train (299 ms) and the largest model (160.3 KB), since it stores 300 trees although each tree has only three nodes; SVM needed 2.2–3.9 KB and E1 0.22 KB. Hybrid E3 adds protocol extraction to the classifier cost without improving detection. The perfect scores do not show that the detectors are secure, because the protocol features depend on how the classes were built (Section 4.5). Detection also waits for a whole session, which lasts a median of 37 s in S2 and 6 s in S3, more than 250 times the slowest computation. Because we measured on a server CPU and not on an ESP32, the results support computational feasibility, not real-time embedded detection.

Table 7. Detection performance and computational cost per session (mean ± SD)

| Method | Recall | FPR | Processing (ms/session) | Training (ms) | Inference (ms/decision) | Model size (KB) |
|---|---|---|---|---|---|---|
| MB/MCM (E1) | 1.000 | 0.000 | 4.55 ± 0.85 | 8.61 ± 2.89 | 0.11 ± 0.03 | 0.22 ± 0.00 |
| RF (E2) | 1.000 | 0.000 | < 0.001 | 298.69 ± 40.53 | 16.49 ± 2.34 | 160.31 ± 0.00 |
| SVM (E2) | 1.000 | 0.000 | < 0.001 | 5.88 ± 1.57 | 1.19 ± 0.36 | 2.20 ± 0.01 |
| Hybrid – RF (E3) | 1.000 | 0.000 | 4.55 ± 0.85 | 328.72 ± 50.60 | 17.39 ± 0.76 | 160.60 ± 0.00 |
| Hybrid – SVM (E3) | 1.000 | 0.000 | 4.55 ± 0.85 | 6.84 ± 1.42 | 1.40 ± 0.30 | 3.93 ± 0.15 |

Note. Data were split by physical tag (6 training, 3 validation and 3 test tags) with five seeds. Recall and FPR: five splits (SD = 0). Processing: building one session's feature vector, over 216 sessions. Training: one fit on the training set; inference: one decision for one session; model size: pickled model; each over five seeds. All values come from one run on 4 vCPU Intel Xeon 2.10 GHz, Python 3.11, scikit-learn 1.9 [26].

## 5.1. Answer to RQ3 (replaces "The study did not measure computational time or model size")

RQ3: Does the security benefit come with an acceptable computational overhead? The computational overhead is acceptable for checkpoint deployment. With feature extraction included, one decision took 1.2–21.9 ms per session on a server CPU. Training took about 0.3 s for RF and under 10 ms for the other methods, and the largest model (RF) was 160.3 KB, while E1 and SVM needed 0.2–3.9 KB (Table 7). These costs are small next to the 6–37 s needed to observe a session. The security benefit is not established, however, because the perfect scores in RQ1 and RQ2 reflect how the dataset was built. RQ3 therefore shows computational feasibility only; ESP32 deployment and real-time detection were not tested.

## Related sentence in Future Work

"So far, we have only tested on Google Colab." → "So far, costs were measured only on a server CPU."

---

Source: Part J (Cell 30) of `../notebooks/RFID_Evidence_Ablation_Colab_1_RQ3.ipynb`, which measures every value in Table 7 in a single run and prints the table in this format. Every split in the notebook groups samples by the 12 physical tags; S3 sessions are mapped to their tag through `data/plans/s3_plan.csv` (pairs P1–P3 → TAG01, …, P34–P36 → TAG12), and the notebook checks that each mapped tag carries a single UID. Per-seed values are saved to `rq3_table7_runs.csv` and the summary to `rq3_table7_summary.csv`. The value in parentheses in the earlier table, e.g. `23.04 (0.49)`, was the per-sample time for batch prediction, not an SD. If the paper reports Colab as the environment, re-run the notebook on Colab and replace every number in the table, the text and the RQ3 answer with that run's output.
