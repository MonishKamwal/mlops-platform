import pandas as pd

from src.features import build_features


def make_df() -> pd.DataFrame:
    return pd.DataFrame({"date": ["2024-01-01", "2024-01-06", "2024-01-07"], "demand": [100, 120, 90]})


def test_build_features_time_columns():
    X, _ = build_features(make_df())
    assert "dayofweek" in X.columns
    assert "month" in X.columns
    assert "is_weekend" in X.columns


def test_build_features_weekend_flag():
    X, _ = build_features(make_df())
    # 2024-01-06 is Saturday (dayofweek=5), 2024-01-07 is Sunday (dayofweek=6)
    assert X["is_weekend"].iloc[1] == 1
    assert X["is_weekend"].iloc[2] == 1


def test_build_features_target_excluded():
    X, y = build_features(make_df())
    assert "demand" not in X.columns
    assert len(y) == 3
