import os

import mlflow.lightgbm
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

_model = None


def get_model():
    global _model
    if _model is None:
        uri = os.environ["FORECAST_MODEL_URI"]
        _model = mlflow.lightgbm.load_model(uri)
    return _model


class ForecastRequest(BaseModel):
    features: dict[str, float]


class ForecastResponse(BaseModel):
    predicted_demand: float


@router.post("/forecast", response_model=ForecastResponse)
def predict_forecast(request: ForecastRequest) -> ForecastResponse:
    model = get_model()
    X = np.array(list(request.features.values())).reshape(1, -1)
    pred = float(model.predict(X)[0])
    return ForecastResponse(predicted_demand=round(pred, 2))
