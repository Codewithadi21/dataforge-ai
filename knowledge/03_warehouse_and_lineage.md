# Data engineering architecture and SQL safety
## Field-level lineage
Lineage traces producer events through raw staging, curated transformations, features, model inference and downstream analytics decisions. Declared lineage may be incomplete; verify graph edges against actual transformations and job logs.
## Safe BigQuery SQL
DataForge restricts SQL plans to a subset of one-table SELECT queries on allow-listed fully qualified BigQuery tables, with approved columns and row limits. The optional Google Cloud integration invokes BigQuery dry_run only, never a live SELECT or any write. A dry run estimates processing bytes and is not proof that a query is free of cost or that IAM access is safe.
## Incremental ETL design
For reliable incremental pipelines, track watermarks, deduplicate event keys, handle late arrivals, maintain idempotency, retry transient failures, enforce schema contracts, log run status and inspect partition strategy. These are architecture recommendations, not deployed DataForge functionality.
## Project scoping
Each connector must be registered under an authorized project ID. Source files and table schemas belong to one project; data from an unrelated project should never be used to answer another project's question.
