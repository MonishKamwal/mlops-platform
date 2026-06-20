from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from api.routers import forecast, fraud, sentiment

app = FastAPI(title="MLOps Platform API", version="0.1.0")

Instrumentator().instrument(app).expose(app)

app.include_router(fraud.router, prefix="/predict", tags=["fraud"])
app.include_router(sentiment.router, prefix="/predict", tags=["sentiment"])
app.include_router(forecast.router, prefix="/predict", tags=["forecast"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
