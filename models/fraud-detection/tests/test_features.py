import pandas as pd
import pytest

from src.features import build_features


def make_df(n: int = 4) -> pd.DataFrame:
    return pd.DataFrame(
        {"V1": range(n), "V2": range(n), "Amount": range(n), "Class": [0, 1] * (n // 2)}
    )


def test_build_features_shape():
    X, y = build_features(make_df())
    assert X.shape == (4, 3)
    assert len(y) == 4


def test_build_features_target_excluded():
    X, y = build_features(make_df())
    assert X.shape[1] == 3  # V1, V2, Amount — Class removed


def test_build_features_returns_series():
    _, y = build_features(make_df())
    assert hasattr(y, "values")
