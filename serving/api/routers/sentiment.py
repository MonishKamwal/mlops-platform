import os

import mlflow.transformers
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        uri = os.environ.get("SENTIMENT_MODEL_URI")
        if not uri:
            raise HTTPException(status_code=503, detail="Sentiment model not configured — train and register a model first")
        _pipeline = mlflow.transformers.load_model(uri)
    return _pipeline


class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    label: str
    score: float


@router.post("/sentiment", response_model=SentimentResponse)
def predict_sentiment(request: SentimentRequest) -> SentimentResponse:
    pipeline = get_pipeline()
    result = pipeline(request.text)[0]
    return SentimentResponse(label=result["label"].lower(), score=round(result["score"], 4))
