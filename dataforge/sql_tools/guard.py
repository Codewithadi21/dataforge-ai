"""Deliberately narrow BigQuery SQL draft and validation grammar.

Not a general SQL parser: rejects joins, subqueries, scripts, functions, strings,
comments, DDL/DML, and anything outside the documented single-table SELECT subset.
This conservative design avoids interpreting arbitrary user SQL as safe.
"""
import re
from typing import Any
from dataforge.connectors.base import ProjectAdapter

_IDENT = r"[a-zA-Z_][a-zA-Z_0-9]*"
_PROJECTION = rf"(?:{_IDENT}|COUNT\s*\(\s*\*\s*\)\s+AS\s+row_count)(?:\s*,\s*{_IDENT})*"
_SQL_PATTERN = re.compile(
    rf"\A\s*SELECT\s+(?P<projection>{_PROJECTION})\s+FROM\s+`(?P<table>[a-zA-Z0-9_\-]+\.{_IDENT}\.{_IDENT})`"
    rf"(?:\s+WHERE\s+(?P<lhs>{_IDENT})\s*(?P<operator>!=|=|<>)\s*(?P<rhs>{_IDENT}))?"
    rf"(?:\s+LIMIT\s+(?P<limit>[0-9]{{1,3}}))?\s*;?\s*\Z",
    flags=re.IGNORECASE,
)

class SQLPolicyError(ValueError):
    """SQL outside the minimum read-only grammar."""


def validate_sql(sql: str, adapter: ProjectAdapter) -> dict[str, Any]:
    if len(sql) > 4000 or "--" in sql or "/*" in sql or "*/" in sql or "\x00" in sql:
        raise SQLPolicyError("SQL rejected: comments, unsupported syntax or oversized text")
    match = _SQL_PATTERN.fullmatch(sql)
    if not match:
        raise SQLPolicyError("Only a single, restricted SELECT from one fully-qualified, backticked approved table is allowed")
    table = match.group("table")
    schema = adapter.get_schema(table)
    if schema is None:
        raise SQLPolicyError(f"Table is not allow-listed: {table}")
    columns = {x["name"].lower() for x in schema.get("columns", [])}
    fields = [x.strip() for x in match.group("projection").split(",")]
    for field in fields:
        if re.fullmatch(r"COUNT\s*\(\s*\*\s*\)\s+AS\s+row_count", field, flags=re.I):
            continue
        if field.lower() not in columns:
            raise SQLPolicyError(f"Unknown or blocked projection: {field}")
    if match.group("lhs"):
        lhs, rhs = match.group("lhs").lower(), match.group("rhs").lower()
        if lhs not in columns or rhs not in columns:
            raise SQLPolicyError("WHERE must compare two known schema columns")
    limit = int(match.group("limit")) if match.group("limit") is not None else None
    if limit is not None and not 1 <= limit <= 500:
        raise SQLPolicyError("LIMIT must be between 1 and 500")
    if not re.search(r"\bCOUNT\s*\(", match.group("projection"), flags=re.I) and limit is None:
        raise SQLPolicyError("All row-level queries require LIMIT <= 500")
    return {"status": "passed", "read_only": True, "strict_subset_only": True,
            "table": table, "approved_columns": fields, "limit": limit,
            "dry_run_executed": False}


def draft_sql(question: str, adapter: ProjectAdapter) -> str:
    tables = adapter.list_available_tables()
    if not tables:
        raise SQLPolicyError("No approved tables available")
    q = question.lower()
    table = next((x for x in tables if x.lower() in q or x.split(".")[-1].lower() in q), tables[0])
    if any(s in q for s in ("flip", "changed prediction", "prediction changed")):
        table = next((t for t in tables if "paired_prediction_replay" in t), table)
        schema = adapter.get_schema(table) or {}
        names = {x["name"] for x in schema.get("columns", [])}
        if {"customer_id", "baseline_prediction", "shifted_prediction"} <= names:
            before, after = "baseline_prediction", "shifted_prediction"
        elif {"customer_id", "predicted_churn_before", "predicted_churn_after"} <= names:
            before, after = "predicted_churn_before", "predicted_churn_after"
        else:
            raise SQLPolicyError("Prediction flip template requires approved replay columns")
        return (f"SELECT customer_id, {before}, {after} "
                f"FROM `{table}` WHERE {before} != {after} LIMIT 100")
    if any(s in q for s in ("count", "how many", "total rows")):
        return f"SELECT COUNT(*) AS row_count FROM `{table}`"
    schema = adapter.get_schema(table) or {}
    columns = [c["name"] for c in schema.get("columns", []) if c.get("sensitivity") == "public"][:4]
    if not columns:
        raise SQLPolicyError("No public demo columns approved for preview")
    return f"SELECT {', '.join(columns)} FROM `{table}` LIMIT 25"
