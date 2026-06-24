import argparse

import pandas as pd


def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Structural transforms only — no scaling (scaler is fit in train to avoid leakage)."""
    X = df.drop(columns=["Class", "Time"], errors="ignore")
    y = df["Class"]
    return X, y


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    X, y = prepare_features(df)
    out = X.copy()
    out["Class"] = y
    out.to_parquet(args.output, index=False)
