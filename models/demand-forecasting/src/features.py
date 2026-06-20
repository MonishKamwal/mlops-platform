import pandas as pd


def build_features(df: pd.DataFrame, target_col: str = "demand") -> tuple[pd.DataFrame, pd.Series]:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["dayofweek"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    feature_cols = [c for c in df.columns if c not in [target_col, "date"]]
    return df[feature_cols], df[target_col]
