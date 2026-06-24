import argparse
import json
import os
import pickle

import mlflow
import mlflow.xgboost
from dotenv import find_dotenv, load_dotenv
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.features import prepare_features


def train(data_path: str, n_estimators: int = 100, test_size: float = 0.2) -> None:
    load_dotenv(find_dotenv())
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment("fraud-detection")

    df = pd.read_parquet(data_path)
    X, y = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=42
    )

    # Fit scaler on train only — prevents leakage into test set
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    with mlflow.start_run():
        mlflow.log_params({"n_estimators": n_estimators, "test_size": test_size})

        model = xgb.XGBClassifier(n_estimators=n_estimators, eval_metric="logloss")
        model.fit(X_train_scaled, y_train)

        auc = roc_auc_score(y_test, model.predict_proba(X_test_scaled)[:, 1])
        mlflow.log_metric("roc_auc", auc)
        mlflow.xgboost.log_model(model, name="model", registered_model_name="fraud-detection")

        os.makedirs("model", exist_ok=True)
        model.save_model("model/model.json")
        with open("model/scaler.pkl", "wb") as f:
            pickle.dump(scaler, f)

    with open("metrics.json", "w") as f:
        json.dump({"roc_auc": round(auc, 4)}, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()
    train(args.data_path, args.n_estimators, args.test_size)
