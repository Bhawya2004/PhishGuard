import pandas as pd
from pipeline import process_email
from store import reset, stats

reset()
test = pd.read_csv("data/test.csv").sample(30, random_state=1)

for _, row in test.iterrows():
    body = f"Dear user, please check your account here: {row['url']}"
    out = process_email("someone@example.com", "Account notice", body,
                        true_label=int(row["label"]))
    print(f"{out['status']:12} {out['score']:.2f}  {row['url'][:60]}  (true={row['label']})")

print("\nSummary:", stats())