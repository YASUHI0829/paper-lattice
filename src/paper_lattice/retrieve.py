from __future__ import annotations

import math
import re
from collections import Counter

from .models import Chunk, SearchHit
from .storage import load_chunks


TOKEN_RE = re.compile(r"[a-zA-Z0-9_+\-.]+")


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def bm25_search(query: str, chunks: list[Chunk], top_k: int = 8) -> list[SearchHit]:
    query_terms = tokenize(query)
    if not query_terms or not chunks:
        return []

    tokenized = [tokenize(chunk.text) for chunk in chunks]
    doc_freq: Counter[str] = Counter()
    for terms in tokenized:
        doc_freq.update(set(terms))

    avgdl = sum(len(terms) for terms in tokenized) / max(len(tokenized), 1)
    n_docs = len(chunks)
    k1 = 1.5
    b = 0.75
    hits: list[SearchHit] = []

    for chunk, terms in zip(chunks, tokenized):
        counts = Counter(terms)
        dl = len(terms)
        score = 0.0
        for term in query_terms:
            if term not in counts:
                continue
            idf = math.log(1 + (n_docs - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            numerator = counts[term] * (k1 + 1)
            denominator = counts[term] + k1 * (1 - b + b * dl / max(avgdl, 1))
            score += idf * numerator / denominator
        if score > 0:
            hits.append(SearchHit(chunk=chunk, score=score))

    hits.sort(key=lambda item: item.score, reverse=True)
    return hits[:top_k]


def search_workspace(query: str, workspace: str | None = None, top_k: int = 8) -> list[SearchHit]:
    return bm25_search(query, load_chunks(workspace), top_k=top_k)
