from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics_endpoint_exists():
    resp = client.get("/metrics")
    assert resp.status_code == 200


def test_fraud_predict_no_model():
    resp = client.post("/predict/fraud", json={"features": [0.1] * 29})
    assert resp.status_code == 503


def test_sentiment_predict_no_model():
    resp = client.post("/predict/sentiment", json={"text": "great product"})
    assert resp.status_code == 503


def test_forecast_predict_no_model():
    resp = client.post("/predict/forecast", json={"features": {"dayofweek": 1.0, "month": 6.0}})
    assert resp.status_code == 503
