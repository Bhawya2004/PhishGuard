"""Turn a downloaded email dataset into data/emails_test.csv (sender, subject, body, label).

Usage:
    python src/prepare_emails.py path/to/Phishing_Email.csv --per-class 100
"""
import argparse
from pathlib import Path

import pandas as pd

TEXT_COLS = ["text_combined", "email text", "email_text", "text", "body", "message", "content"]
LABEL_COLS = ["email type", "label", "class", "type", "target"]
SUBJECT_COLS = ["subject"]
SENDER_COLS = ["sender", "from"]


def pick(df, candidates):
    lower = {c.lower().strip(): c for c in df.columns}
    for name in candidates:
        if name in lower:
            return lower[name]
    return None


def to_label(v):
    s = str(v).strip().lower()
    if "phish" in s or s in ("1", "true"):
        return 1
    if "safe" in s or "ham" in s or "legit" in s or s in ("0", "false"):
        return 0
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--per-class", type=int, default=100)
    ap.add_argument("--out", default="data/emails_test.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.path)
    text_c, label_c = pick(df, TEXT_COLS), pick(df, LABEL_COLS)
    if not text_c or not label_c:
        raise SystemExit(f"Could not find text/label columns. Columns are: {list(df.columns)}")
    subj_c, send_c = pick(df, SUBJECT_COLS), pick(df, SENDER_COLS)

    out = pd.DataFrame({
        "sender": df[send_c].astype(str) if send_c else "unknown",
        "subject": df[subj_c].astype(str) if subj_c else "",
        "body": df[text_c].astype(str).str.strip().str.slice(0, 3000),
        "label": df[label_c].map(to_label),
    })
    out = out.dropna(subset=["label"])
    out = out[out["body"].str.len() >= 20]
    out["label"] = out["label"].astype(int)

    n = min(args.per_class, out["label"].value_counts().min())
    parts = [out[out["label"] == k].sample(n, random_state=42) for k in (0, 1)]
    out = pd.concat(parts).sample(frac=1, random_state=42).reset_index(drop=True)
    Path(args.out).parent.mkdir(exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"Saved {len(out)} emails ({n} per class) to {args.out}")


if __name__ == "__main__":
    main()