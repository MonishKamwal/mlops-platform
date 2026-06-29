from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.routers import fraud

FEATURES_29 = [0.0] * 29


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mock_model():
    return MagicMock()


@pytest.fixture()
def mock_scaler():
    s = MagicMock()
    s.transform.return_value = np.zeros((1, 29))
    return s


@pytest.fixture()
def loaded_client(mock_model, mock_scaler):
    with (
        patch.object(fraud, "_model", mock_model),
        patch.object(fraud, "_scaler", mock_scaler),
    ):
        with TestClient(app) as c:
            yield c


def test_predict_fraud_returns_200(loaded_client, mock_model):
    mock_model.predict_proba.return_value = np.array([[0.7, 0.3]])
    resp = loaded_client.post("/predict/fraud", json={"features": FEATURES_29})
    assert resp.status_code == 200


def test_predict_fraud_is_fraud_true(loaded_client, mock_model):
    mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])
    resp = loaded_client.post("/predict/fraud", json={"features": FEATURES_29})
    body = resp.json()
    assert body["is_fraud"] is True
    assert body["fraud_probability"] == 0.8


def test_predict_fraud_is_fraud_false(loaded_client, mock_model):
    mock_model.predict_proba.return_value = np.array([[0.7, 0.3]])
    resp = loaded_client.post("/predict/fraud", json={"features": FEATURES_29})
    body = resp.json()
    assert body["is_fraud"] is False
    assert body["fraud_probability"] == 0.3


def test_predict_fraud_scaler_applied(loaded_client, mock_model, mock_scaler):
    mock_model.predict_proba.return_value = np.array([[0.7, 0.3]])
    loaded_client.post("/predict/fraud", json={"features": FEATURES_29})
    mock_scaler.transform.assert_called_once()


def test_predict_fraud_wrong_feature_count(loaded_client):
    resp = loaded_client.post("/predict/fraud", json={"features": [0.0] * 10})
    assert resp.status_code == 422


def test_predict_fraud_model_not_loaded(client):
    resp = client.post("/predict/fraud", json={"features": FEATURES_29})
    assert resp.status_code == 503
