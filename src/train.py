import os
import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

os.makedirs("models", exist_ok=True)

train = pd.read_csv("data/train_features.csv")
val = pd.read_csv("data/val_features.csv")

PATH_FEATURES = ["path_length", "path_depth", "query_length", "num_params", "num_slashes"]


def get_xy(df, drop=()):
    X = df.drop(columns=["label", *drop])
    return X, df["label"]


def make_models():
    return {
        "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    }


def run(drop=()):
    X_tr, y_tr = get_xy(train, drop)
    X_va, y_va = get_xy(val, drop)
    rows, fitted = [], {}
    for name, model in make_models().items():
        model.fit(X_tr, y_tr)
        pred = model.predict(X_va)
        rows.append({
            "model": name,
            "accuracy": accuracy_score(y_va, pred),
            "precision": precision_score(y_va, pred),
            "recall": recall_score(y_va, pred),
            "f1": f1_score(y_va, pred),
        })
        fitted[name] = model
    return pd.DataFrame(rows).round(4), fitted, list(X_tr.columns)


print("=== All features ===")
results, fitted, cols = run()
print(results.to_string(index=False))

print("\n=== Without path/query features (ablation) ===")
ablation, _, _ = run(drop=PATH_FEATURES)
print(ablation.to_string(index=False))

best_name = results.sort_values("f1", ascending=False).iloc[0]["model"]
print(f"\nBest model: {best_name}")

joblib.dump({"model": fitted[best_name], "columns": cols, "name": best_name}, "models/detector.joblib")
print("Saved models/detector.joblib")

model = fitted[best_name]
if hasattr(model, "feature_importances_"):
    imp = pd.Series(model.feature_importances_, index=cols).sort_values(ascending=False)
    print("\nTop 10 features:")
    print(imp.head(10).round(4).to_string())