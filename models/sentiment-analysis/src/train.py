import argparse

import mlflow
import mlflow.transformers
import numpy as np
from datasets import load_dataset
from sklearn.metrics import accuracy_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)


def compute_metrics(eval_pred: tuple) -> dict:
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {"accuracy": accuracy_score(labels, preds)}


def train(model_name: str = "distilbert-base-uncased", num_epochs: int = 3) -> None:
    dataset = load_dataset("imdb")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize(batch: dict) -> dict:
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=512)

    tokenized = dataset.map(tokenize, batched=True)

    with mlflow.start_run():
        mlflow.log_params({"model_name": model_name, "num_epochs": num_epochs})

        model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
        training_args = TrainingArguments(
            output_dir="./outputs",
            num_train_epochs=num_epochs,
            per_device_train_batch_size=16,
            eval_strategy="epoch",
        )
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized["train"],
            eval_dataset=tokenized["test"],
            compute_metrics=compute_metrics,
        )
        trainer.train()
        results = trainer.evaluate()
        mlflow.log_metrics(results)
        mlflow.transformers.log_model(
            {"model": model, "tokenizer": tokenizer},
            "model",
            registered_model_name="sentiment-analysis",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default="distilbert-base-uncased")
    parser.add_argument("--num-epochs", type=int, default=3)
    args = parser.parse_args()
    train(args.model_name, args.num_epochs)
