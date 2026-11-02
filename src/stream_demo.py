import time
import pandas as pd
from pipeline import process_email
from store import reset

reset()
test = pd.read_csv("data/test.csv").sample(50, random_state=7)
times = []

for i, (_, row) in enumerate(test.iterrows(), 1):
    body = f"Please review your account activity here: {row['url']}"
    out = process_email("sender@example.com", "Account notice", body,
                        url=row["url"], true_label=int(row["label"]))
    times.append(out["ms"])
    print(f"[{i:02}] {out['status']:12} score={out['score']:.2f}  {out['ms']:.1f} ms")
    time.sleep(0.2)

print(f"\nAverage processing time: {sum(times)/len(times):.1f} ms per email")
print(f"Slowest: {max(times):.1f} ms")