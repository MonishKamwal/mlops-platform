import argparse

import lightgbm as lgb
import mlflow
import mlflow.lightgbm
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from src.features import build_features


def train(data_path: str, n_estimators: int = 300, test_size: float = 0.2) -> None:
    df = pd.read_csv(data_path)
    X, y = build_features(df)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)

    with mlflow.start_run():
        mlflow.log_params({"n_estimators": n_estimators, "test_size": test_size})

        model = lgb.LGBMRegressor(n_estimators=n_estimators)
        model.fit(X_train, y_train, eval_set=[(X_test, y_test)])

        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mlflow.log_metrics({"mae": mae, "rmse": rmse})
        mlflow.lightgbm.log_model(model, "model", registered_model_name="demand-forecasting")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--n-estimators", type=int, default=300)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()
    train(args.data_path, args.n_estimators, args.test_size)
