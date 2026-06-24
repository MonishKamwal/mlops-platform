import pandas as pd

from src.features import prepare_features


def make_df(n: int = 4) -> pd.DataFrame:
    return pd.DataFrame({
        "Time": range(n),
        "V1": range(n),
        "V2": range(n),
        "Amount": range(n),
        "Class": [0, 1] * (n // 2),
    })


def test_prepare_features_drops_time_and_class():
    X, y = prepare_features(make_df())
    assert "Time" not in X.columns
    assert "Class" not in X.columns


def test_prepare_features_shape():
    X, y = prepare_features(make_df())
    assert X.shape == (4, 3)  # V1, V2, Amount
    assert len(y) == 4


def test_prepare_features_target_values():
    _, y = prepare_features(make_df())
    assert list(y) == [0, 1, 0, 1]
