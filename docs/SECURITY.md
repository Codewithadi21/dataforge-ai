# Security and limitations

## Defaults

- All data is synthetic, unless the operator supplies a different, approved export.
- All SQL is **drafted only**. The parser deliberately supports a narrow, one-table SELECT subset; it rejects joins, writes, subqueries, UDFs, aliases except `COUNT(*) AS row_count`, unknown columns, SQL comments, scripts, and non-allow-listed tables.
- Row-returning SQL requires LIMIT <= 500. A restricted identifier (`customer_id`) can appear in an explicitly user-requested prediction-flip draft but *actual data is never retrieved*.
- BigQuery requests are disabled by default. When enabled, a `dry_run=True` job requests an estimate. DataForge never fetches rows or executes normal queries.
- Cloud resource bytes estimates are informational, not billing guarantees. BigQuery dry runs on row-security-filtered tables can report 0 bytes.
- Neither the tool nor this prototype is a sufficient defense against a wrongly privileged cloud account. Grant least privilege, protect credentials and verify allow-listed tables.
- The FastAPI demo has **no authentication**. Bind only to `127.0.0.1`. Do not expose it on a public host without auth, TLS, rate limits and project-scoped access enforcement.

## Retrieval safety

Approved file extensions are Markdown, TXT and optionally PDF. Symlinks and files larger than 2 MB are ignored. Documents are untrusted evidence, not instructions. Never ingest employee records, company datasets, keys, PII or proprietary material into a public demo. The optional Qwen adapter labels narratives as generated and retains deterministic source records. Its simple numeric comparison check is not a proof of full factual grounding.

## Limitations

The model backend may require several gigabytes of memory and network access for the first download. An unavailable model results in deterministic fallback. The local evaluation checks routing and citations; it is **not** a human-rated answer-accuracy benchmark. The current DataPulse example uses fabricated fixture metrics. No live BigQuery tables, Colab execution, public deployment, LLM generation or connected production incident was verified while generating this package.

## Deployment review checklist

- [ ] Implement authentication and scoped authorization.
- [ ] Redact logs; encrypt retained chat histories and restrict retention.
- [ ] Limit and monitor requests and GPU usage.
- [ ] Review all exposed file sources and table schemas.
- [ ] Establish cloud credentials through approved identity mechanisms.
- [ ] Run security tests, adversarial prompt-injection evaluations and incident response exercises.
- [ ] Remove all dummy examples before connecting real business data.
