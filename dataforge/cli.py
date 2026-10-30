"""Offline CLI and reproducible golden evaluation."""
import argparse
import json
from pathlib import Path
from dataforge.assistant.engine import DataForgeEngine
from dataforge.schemas import AskRequest


def evaluate(engine: DataForgeEngine, questions_file: Path) -> dict:
    cases = json.loads(questions_file.read_text(encoding="utf-8"))
    results = []
    for case in cases:
        response = engine.ask(AskRequest(question=case["question"]))
        ok_intent = response.intent == case["expected_intent"]
        expected_source = case.get("expected_source_prefix")
        ok_source = not expected_source or any(c.source_id.startswith(expected_source) for c in response.supporting_sources)
        expected_unsupported = case.get("expect_unsupported", False)
        ok_unsupported = (not expected_unsupported or response.intent == "unsupported")
        results.append({"question": case["question"], "passed": ok_intent and ok_source and ok_unsupported,
                        "actual_intent": response.intent, "sources": [c.source_id for c in response.supporting_sources]})
    return {"total": len(results), "passed": sum(x["passed"] for x in results), "cases": results,
            "note": "Routing/citation smoke evaluation only; not an independently verified factual accuracy metric."}


def main() -> None:
    ap = argparse.ArgumentParser(description="DataForge AI local tools")
    ap.add_argument("command", choices=["ask", "eval", "status"])
    ap.add_argument("question", nargs="?", default="How does DataPulse work?")
    ap.add_argument("--sql", default=None)
    ap.add_argument("--cloud-dry-run", action="store_true")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()
    engine = DataForgeEngine()
    if args.command == "status":
        result = {"registered_projects": engine.registry.available(), "backend": engine.settings.model_backend,
                  "knowledge_chunks": len(engine.index.chunks)}
    elif args.command == "eval":
        root = Path(__file__).resolve().parents[1]
        result = evaluate(engine, root / "eval" / "golden_questions.json")
    else:
        result = engine.ask(AskRequest(question=args.question, sql=args.sql, cloud_dry_run=args.cloud_dry_run)).model_dump()
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    print(output)

if __name__ == "__main__":
    main()
