from transformers import AutoTokenizer


def tokenize_texts(texts: list[str], model_name: str = "distilbert-base-uncased") -> dict:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return tokenizer(texts, truncation=True, padding=True, return_tensors="pt")
