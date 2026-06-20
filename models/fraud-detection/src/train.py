import argparse

import mlflow
import mlflow.xgboost
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from src.features import build_features


def train(data_path: str, n_estimators: int = 100, test_size: float = 0.2) -> None:
    df = pd.read_csv(data_path)
    X, y = build_features(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=42
    )

    with mlflow.start_run():
        mlflow.log_params({"n_estimators": n_estimators, "test_size": test_size})

        model = xgb.XGBClassifier(n_estimators=n_estimators, eval_metric="logloss")
        model.fit(X_train, y_train)

        auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
        mlflow.log_metric("roc_auc", auc)
        mlflow.xgboost.log_model(model, "model", registered_model_name="fraud-detection")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()
    train(args.data_path, args.n_estimators, args.test_size)
