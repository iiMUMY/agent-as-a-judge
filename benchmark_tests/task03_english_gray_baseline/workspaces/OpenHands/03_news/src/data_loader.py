import re
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer


def clean_text(text):
    text = re.sub(r"[^a-zA-Z\\s]", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text


def load_data_with_tfidf():
    data = fetch_20newsgroups(subset="train")
    cleaned = [clean_text(x) for x in data.data]
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(cleaned)
    return X, data.target
