# Incident investigation and data drift
## Incident response steps
An incident investigator should read the timestamp and affected assets, inspect source schema validation, check pipeline freshness and volume, compare cohort-fixed before and after prediction replay, inspect drift indicators, trace feature lineage, and propose checks for a human reviewer. Do not autonomously modify data or retrain a model.
## Schema drift versus semantic drift
Schema drift changes physical structure such as missing columns, types or names. Semantic drift changes a field's business meaning despite a stable schema, such as redefining engagement_score. A passed schema check does not establish semantic correctness.
## PSI and KS
Population Stability Index (PSI) summarizes how a binned distribution changed across snapshots. KS compares empirical cumulative distributions. Metrics may indicate a distribution difference but do not, by themselves, establish causal model harm.
## False positives and false negatives
Incident thresholds may produce false positive alerts when data variation is benign, and false negatives when checks miss an actual issue. Validate affected cohorts and business impact before remediation decisions.
## Runbook and approvals
Every correction or remediation remains outside DataForge's scope. DataForge provides read-only evidence, caveats, reproducible checks and a visible human-approval boundary.
