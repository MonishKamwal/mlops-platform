import os
import pickle

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

router = APIRouter()

# V1–V28 + Amount; Time and Class are dropped in the featurize step
EXPECTED_FEATURES = 29

_model = None
_scaler = None


def load_artifacts() -> None:
    """Load XGBoost model and scaler from FRAUD_MODEL_DIR (local files) or
    FRAUD_MODEL_URI + FRAUD_SCALER_PATH (MLflow registry, for AKS).
    Called once at app startup via lifespan."""
    global _model, _scaler

    model_dir = os.environ.get("FRAUD_MODEL_DIR")
    model_uri = os.environ.get("FRAUD_MODEL_URI")

    if model_dir:
        import xgboost as xgb

        m = xgb.XGBClassifier()
        m.load_model(os.path.join(model_dir, "model.json"))
        with open(os.path.join(model_dir, "scaler.pkl"), "rb") as f:
            s = pickle.load(f)
        _model, _scaler = m, s

    elif model_uri:
        import mlflow.xgboost

        scaler_path = os.environ.get("FRAUD_SCALER_PATH")
        if not scaler_path:
            raise RuntimeError(
                "FRAUD_MODEL_URI is set but FRAUD_SCALER_PATH is not — "
                "the scaler must be provided separately when loading from MLflow"
            )
        _model = mlflow.xgboost.load_model(model_uri)
        with open(scaler_path, "rb") as f:
            _scaler = pickle.load(f)

    # If neither env var is set, _model/_scaler stay None and the endpoint returns 503.


class FraudRequest(BaseModel):
    features: list[float]

    @field_validator("features")
    @classmethod
    def check_length(cls, v: list[float]) -> list[float]:
        if len(v) != EXPECTED_FEATURES:
            raise ValueError(f"Expected {EXPECTED_FEATURES} features, got {len(v)}")
        return v


class FraudResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool


@router.post("/fraud", response_model=FraudResponse)
def predict_fraud(request: FraudRequest) -> FraudResponse:
    if _model is None or _scaler is None:
        raise HTTPException(
            status_code=503,
            detail="Fraud model not loaded — set FRAUD_MODEL_DIR or FRAUD_MODEL_URI + FRAUD_SCALER_PATH",
        )
    X = np.array(request.features).reshape(1, -1)
    X_scaled = _scaler.transform(X)
    proba = float(_model.predict_proba(X_scaled)[0][1])
    return FraudResponse(fraud_probability=round(proba, 4), is_fraud=proba > 0.5)
