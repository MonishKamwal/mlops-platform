import os

import mlflow.xgboost
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_model = None


def get_model():
    global _model
    if _model is None:
        uri = os.environ["FRAUD_MODEL_URI"]
        _model = mlflow.xgboost.load_model(uri)
    return _model


class FraudRequest(BaseModel):
    features: list[float]


class FraudResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool


@router.post("/fraud", response_model=FraudResponse)
def predict_fraud(request: FraudRequest) -> FraudResponse:
    model = get_model()
    X = np.array(request.features).reshape(1, -1)
    proba = float(model.predict_proba(X)[0][1])
    return FraudResponse(fraud_probability=round(proba, 4), is_fraud=proba > 0.5)
