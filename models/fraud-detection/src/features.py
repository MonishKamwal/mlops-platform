import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def build_features(df: pd.DataFrame) -> tuple[np.ndarray, pd.Series]:
    X = df.drop(columns=["Class"])
    y = df["Class"]
    X_scaled = StandardScaler().fit_transform(X)
    return X_scaled, y
