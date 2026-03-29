"""Generate validation tests from automatically generated requirements.

Input:
- spec/spec_auto.md

Output:
- tests/tests_auto.json

Each generated test includes:
- unique test ID
- requirement ID reference
- scenario
- steps
- expected result
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_SPEC_PATH = BASE_DIR / "spec" / "spec_auto.md"
OUTPUT_TESTS_PATH = BASE_DIR / "tests" / "tests_auto.json"


REQ_PATTERN = re.compile(
	r"# Requirement ID:\s*(FR_auto_\d+)\s*\n"
	r"- Description:\s*\[(.*?)\]\s*\n"
	r"- Source Persona:\s*\[(.*?)\]\s*\n"
	r"- Traceability:\s*\[(.*?)\]\s*\n"
	r"- Acceptance Criteria:\s*\[(.*?)\]",
	re.DOTALL,
)


def parse_requirements(spec_text: str) -> List[Dict[str, str]]:
	reqs: List[Dict[str, str]] = []
	for match in REQ_PATTERN.finditer(spec_text):
		requirement_id, description, persona, traceability, acceptance = match.groups()
		reqs.append(
			{
				"requirement_id": requirement_id.strip(),
				"description": " ".join(description.split()),
				"source_persona": " ".join(persona.split()),
				"traceability": " ".join(traceability.split()),
				"acceptance_criteria": " ".join(acceptance.split()),
			}
		)
	return reqs


def scenario_for_requirement(description: str) -> str:
	desc = description.lower()
	if "quick start" in desc:
		return "Verify sleep quick start launches content promptly"
	if "search results" in desc or "category labels" in desc:
		return "Verify search relevance and filter refinement behavior"
	if "filter" in desc:
		return "Verify sleep filters constrain result set"
	if "short sleep" in desc:
		return "Verify short sleep collection lists brief sessions"
	if "recommend" in desc and "mood" in desc:
		return "Verify mood and time based recommendations"
	if "favorites" in desc:
		return "Verify saved meditation is available in Favorites"
	if "pricing" in desc or "trial" in desc or "renewal" in desc:
		return "Verify subscription billing details before confirmation"
	if "cancellation" in desc:
		return "Verify in-app cancellation flow and confirmation"
	if "billing history" in desc:
		return "Verify billing history entries contain charge details"
	if "playback controls" in desc or "volume" in desc:
		return "Verify playback controls update audio behavior"
	if "narrator" in desc and "search" in desc:
		return "Verify narrator search opens narrator content page"
	if "updates" in desc or "reliability" in desc:
		return "Verify core workflows remain stable after update"
	return "Verify requirement behavior in standard usage flow"


def steps_for_requirement(req: Dict[str, str]) -> List[str]:
	desc = req["description"].lower()
	steps = ["Launch the application and sign in with a valid user account."]

	if "quick start" in desc:
		steps.extend(
			[
				"Navigate to the home or sleep entry screen.",
				"Select the Sleep Quick Start action.",
				"Observe content start behavior and prompt flow.",
			]
		)
	elif "search results" in desc or "category labels" in desc:
		steps.extend(
			[
				"Run a keyword search from the main search interface.",
				"Inspect initial relevance of returned results.",
				"Apply category filters and verify refined results update correctly.",
			]
		)
	elif "filter" in desc:
		steps.extend(
			[
				"Open sleep browsing and apply narrator, duration, and content-type filters.",
				"Submit filtering options and load results.",
				"Inspect returned items for filter alignment.",
			]
		)
	elif "short sleep" in desc:
		steps.extend(
			[
				"Open the short sleep collection.",
				"Review listed session durations.",
				"Confirm the majority of entries are brief sessions.",
			]
		)
	elif "recommend" in desc and "mood" in desc:
		steps.extend(
			[
				"Open recommendations and choose a mood and time budget.",
				"Request personalized recommendations.",
				"Inspect recommendation relevance to both inputs.",
			]
		)
	elif "favorites" in desc:
		steps.extend(
			[
				"Open a meditation session and mark it as favorite.",
				"Navigate to the Favorites section.",
				"Open the saved item and start playback.",
			]
		)
	elif "pricing" in desc or "trial" in desc or "renewal" in desc:
		steps.extend(
			[
				"Start a subscription or trial flow and proceed to the confirmation stage.",
				"Inspect visible billing details before final confirmation.",
				"Verify presence of price, trial terms, and renewal timing.",
			]
		)
	elif "cancellation" in desc:
		steps.extend(
			[
				"Open subscription settings and initiate cancellation.",
				"Complete all required cancellation actions.",
				"Observe final confirmation message and subscription status.",
			]
		)
	elif "billing history" in desc:
		steps.extend(
			[
				"Open the billing history page.",
				"Review at least one recent charge entry.",
				"Verify date, amount, and charge type fields are present.",
			]
		)
	elif "playback controls" in desc or "volume" in desc:
		steps.extend(
			[
				"Start guided playback content.",
				"Adjust narrator volume, background volume, and speed controls.",
				"Observe whether playback output changes accordingly.",
			]
		)
	elif "narrator" in desc and "search" in desc:
		steps.extend(
			[
				"Open search and submit a narrator name query.",
				"Open the narrator-specific result or profile page.",
				"Review listed related sessions in that view.",
			]
		)
	elif "updates" in desc or "reliability" in desc:
		steps.extend(
			[
				"Install or launch the latest application build.",
				"Execute startup, login, search, and playback workflows.",
				"Observe whether any blocking failures occur.",
			]
		)
	else:
		steps.extend(
			[
				"Navigate to the feature area related to the requirement.",
				"Perform user actions described by the requirement.",
				"Observe whether system behavior matches expected behavior.",
			]
		)

	return steps


def build_tests(requirements: List[Dict[str, str]]) -> List[Dict[str, object]]:
	tests: List[Dict[str, object]] = []
	for idx, req in enumerate(requirements, start=1):
		tests.append(
			{
				"test_id": f"T_auto_{idx:02d}",
				"requirement_id": req["requirement_id"],
				"scenario": scenario_for_requirement(req["description"]),
				"steps": steps_for_requirement(req),
				"expected_result": req["acceptance_criteria"],
			}
		)
	return tests


def main() -> None:
	if not INPUT_SPEC_PATH.exists():
		raise FileNotFoundError(f"Missing input specification: {INPUT_SPEC_PATH}")

	spec_text = INPUT_SPEC_PATH.read_text(encoding="utf-8")
	requirements = parse_requirements(spec_text)
	if not requirements:
		raise ValueError("No requirements parsed from spec/spec_auto.md")

	tests = build_tests(requirements)
	payload = {"tests": tests}

	OUTPUT_TESTS_PATH.parent.mkdir(parents=True, exist_ok=True)
	with OUTPUT_TESTS_PATH.open("w", encoding="utf-8") as f:
		json.dump(payload, f, indent=2, ensure_ascii=False)

	print(f"Wrote: {OUTPUT_TESTS_PATH}")
	print(f"Parsed requirements: {len(requirements)}")
	print(f"Generated tests: {len(tests)}")


if __name__ == "__main__":
	main()