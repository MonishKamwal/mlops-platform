import argparse

import mlflow.xgboost
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score

from src.features import build_features


def evaluate(model_uri: str, data_path: str) -> dict:
    model = mlflow.xgboost.load_model(model_uri)
    df = pd.read_csv(data_path)
    X, y = build_features(df)
    preds = model.predict(X)
    proba = model.predict_proba(X)[:, 1]
    return {
        "roc_auc": roc_auc_score(y, proba),
        "report": classification_report(y, preds),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-uri", required=True)
    parser.add_argument("--data-path", required=True)
    args = parser.parse_args()
    results = evaluate(args.model_uri, args.data_path)
    print(results["report"])
    print(f"ROC AUC: {results['roc_auc']:.4f}")
