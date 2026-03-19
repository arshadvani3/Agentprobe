"""
ChromaDB vector store for test case deduplication.

Every test case (from YAML suites and LLM generation) is stored as an embedding.
Before adding a newly generated test, we check semantic similarity against the store —
if a nearly-identical test already exists, we skip it. This ensures each evaluation
generates genuinely novel coverage rather than regenerating the same scenarios.

Distance metric: cosine (0 = identical, 2 = completely opposite).
Duplicate threshold: distance < 0.15 (very similar inputs).
"""
import logging
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

COLLECTION_NAME = "agentprobe_tests"
DUPLICATE_THRESHOLD = 0.15  # cosine distance below this = near-duplicate

_collection: chromadb.Collection | None = None


def init_chroma(path: str) -> None:
    """Initialise ChromaDB. On failure, logs and continues — deduplication is optional."""
    global _collection
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=path)
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB initialised at %s (%d test cases in store)", path, _collection.count()
        )
    except Exception as e:
        logger.warning(
            "ChromaDB init failed (%s) — continuing without semantic deduplication", e
        )
        _collection = None


def seed_from_tests(tests: list[dict], suite_name: str) -> None:
    """
    Upsert test cases into ChromaDB. Safe to call on every startup — uses test ID
    as the document ID so re-seeding the same suite is idempotent.
    """
    if _collection is None or not tests:
        return

    items = [
        (t.get("input", "").strip(), f"{suite_name}__{t.get('id', i)}", t.get("category", ""))
        for i, t in enumerate(tests)
        if t.get("input", "").strip()
    ]
    if not items:
        return

    docs, ids, cats = zip(*items)
    metadatas = [{"category": c, "suite": suite_name} for c in cats]

    try:
        _collection.upsert(
            documents=list(docs),
            ids=list(ids),
            metadatas=list(metadatas),
        )
        logger.info("ChromaDB seeded %d tests from suite '%s'", len(docs), suite_name)
    except Exception as e:
        logger.warning("ChromaDB seed failed for suite '%s': %s", suite_name, e)


def is_duplicate(query: str) -> bool:
    """
    Return True if a semantically near-identical test already exists in the store.
    Falls back to False gracefully if ChromaDB is unavailable or the store is empty.
    """
    if _collection is None or not query.strip():
        return False
    try:
        count = _collection.count()
        if count == 0:
            return False
        results = _collection.query(
            query_texts=[query],
            n_results=1,
            include=["distances"],
        )
        distances = results.get("distances", [[]])[0]
        return bool(distances and distances[0] < DUPLICATE_THRESHOLD)
    except Exception as e:
        logger.warning("ChromaDB duplicate check failed: %s", e)
        return False


def add_tests(tests: list[dict], eval_id: str, category: str) -> None:
    """Store newly generated tests so future evals can deduplicate against them."""
    if _collection is None or not tests:
        return

    items = [
        (t.get("input", "").strip(), f"{eval_id}__{category}__{i}")
        for i, t in enumerate(tests)
        if t.get("input", "").strip()
    ]
    if not items:
        return

    docs, ids = zip(*items)
    metadatas = [{"category": category, "suite": "generated", "eval_id": eval_id}] * len(docs)

    try:
        _collection.add(
            documents=list(docs),
            ids=list(ids),
            metadatas=list(metadatas),
        )
    except Exception as e:
        logger.warning("ChromaDB add_tests failed: %s", e)


def find_similar(query: str, n: int = 3) -> list[dict]:
    """Return the n most similar existing test inputs to the given query."""
    if _collection is None or not query.strip():
        return []
    try:
        count = _collection.count()
        if count == 0:
            return []
        results = _collection.query(
            query_texts=[query],
            n_results=min(n, count),
            include=["documents", "distances", "metadatas"],
        )
        return [
            {
                "input": doc,
                "distance": dist,
                "category": meta.get("category", ""),
                "suite": meta.get("suite", ""),
            }
            for doc, dist, meta in zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0],
            )
        ]
    except Exception as e:
        logger.warning("ChromaDB find_similar failed: %s", e)
        return []
