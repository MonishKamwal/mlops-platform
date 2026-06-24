import argparse
import json
import pickle

import pandas as pd
import xgboost as xgb
from sklearn.metrics import classification_report, roc_auc_score

from src.features import prepare_features


def evaluate(model_path: str, scaler_path: str, data_path: str) -> dict:
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    df = pd.read_parquet(data_path)
    X, y = prepare_features(df)
    X_scaled = scaler.transform(X)

    preds = model.predict(X_scaled)
    proba = model.predict_proba(X_scaled)[:, 1]
    return {
        "roc_auc": roc_auc_score(y, proba),
        "report": classification_report(y, preds),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--scaler-path", required=True)
    parser.add_argument("--data-path", required=True)
    args = parser.parse_args()
    results = evaluate(args.model_path, args.scaler_path, args.data_path)
    print(results["report"])
    print(f"ROC AUC: {results['roc_auc']:.4f}")

    with open("eval_metrics.json", "w") as f:
        json.dump({"roc_auc": round(results["roc_auc"], 4)}, f)
