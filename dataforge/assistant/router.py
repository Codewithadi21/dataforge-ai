"""Deterministic, explicit intent routing (no autonomous tools)."""

def classify(question: str, sql: str | None = None) -> str:
    q = question.lower().strip()
    # Educational definitions should retrieve documentation, not trigger a tool.
    if not sql and (q.startswith("how is ") or q.startswith("what is field level lineage")):
        return "guide"
    if sql or q.startswith(("preview ", "show customers whose predictions flipped", "count rows")) or any(w in q for w in ("sql", "query", "bigquery", "select ", "rows", "prediction flips query")):
        return "sql"
    if any(w in q for w in ("lineage", "upstream", "downstream", "trace", "depends on", "source field")):
        return "lineage"
    if any(w in q for w in ("incident", "root cause", "rca", "drift", "changed", "churn model", "prediction", "anomaly")):
        return "incident"
    return "guide"
