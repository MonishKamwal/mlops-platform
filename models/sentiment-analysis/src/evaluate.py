import argparse

import mlflow.transformers
from sklearn.metrics import accuracy_score, classification_report


def evaluate(model_uri: str, texts: list[str], labels: list[int]) -> dict:
    pipeline = mlflow.transformers.load_model(model_uri)
    results = pipeline(texts)
    preds = [1 if r["label"] == "POSITIVE" else 0 for r in results]
    return {
        "accuracy": accuracy_score(labels, preds),
        "report": classification_report(labels, preds, target_names=["negative", "positive"]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-uri", required=True)
    args = parser.parse_args()
    # Example usage — replace with real evaluation data
    sample_texts = ["I loved this!", "Absolutely terrible."]
    sample_labels = [1, 0]
    results = evaluate(args.model_uri, sample_texts, sample_labels)
    print(results["report"])
