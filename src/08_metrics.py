"""Compute pipeline metrics for the automated SpecChain pipeline.

This script computes automated-pipeline metrics and writes:
- metrics/metrics_auto.json

Metrics computed:
- dataset_size
- persona_count
- requirements_count
- tests_count
- traceability_links
- review_coverage
- traceability_ratio
- testability_rate
- ambiguity_ratio
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Set


BASE_DIR = Path(__file__).resolve().parents[1]

REVIEWS_CLEAN_PATH = BASE_DIR / "data" / "reviews_clean.jsonl"
REVIEW_GROUPS_AUTO_PATH = BASE_DIR / "data" / "review_groups_auto.json"
PERSONAS_AUTO_PATH = BASE_DIR / "personas" / "personas_auto.json"
SPEC_AUTO_PATH = BASE_DIR / "spec" / "spec_auto.md"
TESTS_AUTO_PATH = BASE_DIR / "tests" / "tests_auto.json"
OUTPUT_PATH = BASE_DIR / "metrics" / "metrics_auto.json"


AMBIGUOUS_TERMS = {
	"fast",
	"quick",
	"easy",
	"easily",
	"better",
	"best",
	"user-friendly",
	"friendly",
	"simple",
	"smooth",
	"intuitive",
	"minimal",
	"reasonable",
	"reasonably",
	"mostly",
	"fairly",
	"quickly",
	"clear",
	"clearly",
}


def read_json(path: Path):
	with path.open("r", encoding="utf-8-sig") as f:
		return json.load(f)


def count_jsonl_rows(path: Path) -> int:
	count = 0
	with path.open("r", encoding="utf-8") as f:
		for line in f:
			if line.strip():
				count += 1
	return count


def parse_requirements(spec_text: str) -> List[Dict[str, str]]:
	lines = spec_text.splitlines()
	requirements: List[Dict[str, str]] = []
	current: Dict[str, str] | None = None

	for raw in lines:
		line = raw.strip()
		if line.startswith("# Requirement ID:"):
			if current:
				requirements.append(current)
			rid = line.split(":", 1)[1].strip()
			current = {
				"requirement_id": rid,
				"description": "",
				"source_persona": "",
				"traceability": "",
				"acceptance_criteria": "",
			}
		elif current and line.startswith("- Description:"):
			current["description"] = line.split(":", 1)[1].strip()
		elif current and line.startswith("- Source Persona:"):
			current["source_persona"] = line.split(":", 1)[1].strip()
		elif current and line.startswith("- Traceability:"):
			current["traceability"] = line.split(":", 1)[1].strip()
		elif current and line.startswith("- Acceptance Criteria:"):
			current["acceptance_criteria"] = line.split(":", 1)[1].strip()

	if current:
		requirements.append(current)

	return requirements


def contains_ambiguous_language(text: str) -> bool:
	cleaned = text.lower()
	tokens = set(re.findall(r"[a-zA-Z\-]+", cleaned))
	return any(term in tokens for term in AMBIGUOUS_TERMS)


def compute_automated_metrics() -> Dict[str, float | int | str]:
	dataset_size = count_jsonl_rows(REVIEWS_CLEAN_PATH)

	review_groups_payload = read_json(REVIEW_GROUPS_AUTO_PATH)
	groups = review_groups_payload.get("groups", []) if isinstance(review_groups_payload, dict) else review_groups_payload

	personas_payload = read_json(PERSONAS_AUTO_PATH)
	personas = personas_payload.get("personas", []) if isinstance(personas_payload, dict) else personas_payload
	persona_count = len(personas)

	spec_text = SPEC_AUTO_PATH.read_text(encoding="utf-8")
	requirements = parse_requirements(spec_text)
	requirements_count = len(requirements)

	tests_payload = read_json(TESTS_AUTO_PATH)
	tests = tests_payload.get("tests", [])
	tests_count = len(tests)

	# Links: groups->reviews + personas->groups + requirements->personas + tests->requirements
	group_to_review_links = sum(len(g.get("review_ids", [])) for g in groups)
	persona_to_group_links = sum(1 for p in personas if p.get("derived_from_group"))
	requirement_to_persona_links = sum(1 for r in requirements if r.get("source_persona"))

	valid_requirement_ids: Set[str] = {r.get("requirement_id", "") for r in requirements}
	test_to_requirement_links = sum(1 for t in tests if t.get("requirement_id") in valid_requirement_ids)

	traceability_links = (
		group_to_review_links
		+ persona_to_group_links
		+ requirement_to_persona_links
		+ test_to_requirement_links
	)

	covered_reviews = {rid for g in groups for rid in g.get("review_ids", [])}
	review_coverage = (len(covered_reviews) / dataset_size) if dataset_size else 0.0

	traceable_requirements = sum(1 for r in requirements if r.get("source_persona"))
	traceability_ratio = (traceable_requirements / requirements_count) if requirements_count else 0.0

	test_counts_by_req: Dict[str, int] = {}
	for t in tests:
		rid = t.get("requirement_id")
		if rid:
			test_counts_by_req[rid] = test_counts_by_req.get(rid, 0) + 1
	testable_requirements = sum(1 for r in requirements if test_counts_by_req.get(r.get("requirement_id", ""), 0) >= 1)
	testability_rate = (testable_requirements / requirements_count) if requirements_count else 0.0

	ambiguous_requirements = 0
	for r in requirements:
		combined = f"{r.get('description', '')} {r.get('acceptance_criteria', '')}"
		if contains_ambiguous_language(combined):
			ambiguous_requirements += 1
	ambiguity_ratio = (ambiguous_requirements / requirements_count) if requirements_count else 0.0

	return {
		"pipeline": "automated",
		"dataset_size": dataset_size,
		"persona_count": persona_count,
		"requirements_count": requirements_count,
		"tests_count": tests_count,
		"traceability_links": traceability_links,
		"review_coverage": round(review_coverage, 4),
		"traceability_ratio": round(traceability_ratio, 4),
		"testability_rate": round(testability_rate, 4),
		"ambiguity_ratio": round(ambiguity_ratio, 4),
	}


def main() -> None:
	metrics = compute_automated_metrics()
	OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
	with OUTPUT_PATH.open("w", encoding="utf-8") as f:
		json.dump(metrics, f, indent=2)
	print(f"Wrote: {OUTPUT_PATH}")
	print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
	main()