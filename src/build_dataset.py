import pandas as pd
import random
from sklearn.model_selection import train_test_split

random.seed(42)

# 1. Phishing URLs
phish = pd.read_csv("data/verified_online.csv")[["url"]].dropna().drop_duplicates()
phish["label"] = 1

# 2. Safe URLs from top sites (use top 100k, not obscure tail)
top = pd.read_csv("data/top-1m.csv", header=None, names=["rank", "domain"])
top = top.head(100_000)

paths = ["", "", "/", "/login", "/account", "/about", "/contact",
         "/products/12345", "/search?q=shoes", "/blog/2024/news",
         "/help/support", "/signin", "/cart", "/user/profile"]

def make_safe_url(domain):
    scheme = "https://" if random.random() < 0.9 else "http://"
    www = "www." if random.random() < 0.5 else ""
    return f"{scheme}{www}{domain}{random.choice(paths)}"

n = min(len(phish), 10_000)
phish = phish.sample(n, random_state=42)
safe = top.sample(n, random_state=42).copy()
safe["url"] = safe["domain"].apply(make_safe_url)
safe = safe[["url"]]
safe["label"] = 0

# 3. Combine, shuffle
df = pd.concat([phish, safe]).sample(frac=1, random_state=42).reset_index(drop=True)

# 4. Split 70 / 15 / 15 (stratified)
train, temp = train_test_split(df, test_size=0.30, stratify=df["label"], random_state=42)
val, test = train_test_split(temp, test_size=0.50, stratify=temp["label"], random_state=42)

train.to_csv("data/train.csv", index=False)
val.to_csv("data/val.csv", index=False)
test.to_csv("data/test.csv", index=False)

print(len(train), len(val), len(test))
print(df["label"].value_counts())