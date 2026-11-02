"""Compare URL-only, LLM-only and combined detection on real emails.

Usage:
    python evaluate_llm.py --limit 200
Needs data/emails_test.csv (see src/prepare_emails.py) and GROQ_API_KEY.
LLM answers are cached in results/llm_cache.json so re-runs do not call the API again.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score)

sys.path.insert(0, str(Path(__file__).parent / "src"))
import llm_agent
from detector import score_url
from pipeline import URL_RE

ap = argparse.ArgumentParser()
ap.add_argument("--limit", type=int, default=200, help="number of emails to evaluate")
ap.add_argument("--delay", type=float, default=2.2, help="seconds between API calls (rate limits)")
ap.add_argument("--threshold", type=float, default=0.7)
args = ap.parse_args()

if not llm_agent.llm_available():
    raise SystemExit("Set GROQ_API_KEY first (and pip install groq).")

Path("results").mkdir(exist_ok=True)
cache_path = Path("results/llm_cache.json")
cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

df = pd.read_csv("data/emails_test.csv").fillna("")
df = df.sample(n=min(args.limit, len(df)), random_state=42)

rows, failures = [], 0
for n, (i, r) in enumerate(df.iterrows(), 1):
    urls = URL_RE.findall(r["body"])
    url_score = max([score_url(u)[0] for u in urls], default=0.0)

    key = str(i)
    res = cache.get(key)
    if res is None:
        res = llm_agent.analyze_email(r["sender"], r["subject"], r["body"], urls)
        if res:
            cache[key] = res
            cache_path.write_text(json.dumps(cache))
        else:
            failures += 1
        time.sleep(args.delay)
    text_risk = res["text_risk"] if res else 0.0

    rows.append({"label": int(r["label"]), "url_score": url_score, "text_risk": text_risk,
                 "combined": max(url_score, text_risk), "has_link": bool(urls),
                 "explanation": res["explanation"] if res else "",
                 "body": r["body"][:200]})
    if n % 10 == 0:
        print(f"{n}/{len(df)} done")

res = pd.DataFrame(rows)
y, th = res["label"], args.threshold


def metrics(name, col):
    pred = (res[col] >= th).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return pred, {"system": name, "TP": tp, "FP": fp, "TN": tn, "FN": fn,
                  "accuracy": accuracy_score(y, pred),
                  "precision": precision_score(y, pred, zero_division=0),
                  "recall": recall_score(y, pred, zero_division=0),
                  "f1": f1_score(y, pred, zero_division=0)}


_, m1 = metrics("URL model only", "url_score")
_, m2 = metrics("LLM only", "text_risk")
pred_c, m3 = metrics("URL + LLM (final)", "combined")
table = pd.DataFrame([m1, m2, m3]).round(3)
table.to_csv("results/llm_comparison.csv", index=False)

print(f"\nEmails evaluated: {len(res)}  |  emails with a link: {int(res['has_link'].sum())}"
      f"  |  threshold {th}")
print(table.to_string(index=False))
if failures:
    print(f"\nWARNING: {failures} emails had no LLM result (counted as text_risk 0). "
          "Re-run to retry them; cached ones are not re-sent.")

plt.figure(figsize=(5, 4))
sns.heatmap(confusion_matrix(y, pred_c, labels=[0, 1]), annot=True, fmt="d", cmap="Purples",
            xticklabels=["Delivered", "Quarantined"], yticklabels=["Safe", "Phishing"])
plt.xlabel("System decision (URL + LLM)")
plt.ylabel("Actual")
plt.title(f"Confusion matrix with LLM layer (threshold {th})")
plt.tight_layout()
plt.savefig("results/confusion_matrix_llm.png", dpi=200)

rescued = res[(res.label == 1) & (res.url_score < th) & (res.combined >= th)]
new_fp = res[(res.label == 0) & (res.url_score < th) & (res.combined >= th)]
print(f"\nPhishing emails the URL model missed but the LLM caught: {len(rescued)}")
print(f"Safe emails the LLM newly flagged (false alarms):        {len(new_fp)}")
pd.concat([rescued.assign(kind="rescued"), new_fp.assign(kind="new_false_alarm")]) \
    .to_csv("results/llm_examples.csv", index=False)
print("Saved results/llm_comparison.csv, confusion_matrix_llm.png, llm_examples.csv")