import argparse

import mlflow.lightgbm
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.features import build_features


def evaluate(model_uri: str, data_path: str) -> dict:
    model = mlflow.lightgbm.load_model(model_uri)
    df = pd.read_csv(data_path)
    X, y = build_features(df)
    preds = model.predict(X)
    return {
        "mae": mean_absolute_error(y, preds),
        "rmse": float(np.sqrt(mean_squared_error(y, preds))),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-uri", required=True)
    parser.add_argument("--data-path", required=True)
    args = parser.parse_args()
    results = evaluate(args.model_uri, args.data_path)
    print(f"MAE: {results['mae']:.4f}  RMSE: {results['rmse']:.4f}")
