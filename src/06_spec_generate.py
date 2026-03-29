"""Generate structured system requirements from automated personas.

Input:
- personas/personas_auto.json

Output:
- spec/spec_auto.md

Each requirement includes:
- unique requirement ID
- behavior description
- source persona
- review-group traceability
- acceptance criteria
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_PERSONAS_PATH = BASE_DIR / "personas" / "personas_auto.json"
OUTPUT_SPEC_PATH = BASE_DIR / "spec" / "spec_auto.md"


@dataclass(frozen=True)
class RequirementTemplate:
	req_key: str
	description: str
	acceptance_criteria: str


TEMPLATES_BY_GROUP: Dict[str, List[RequirementTemplate]] = {
	"G1": [
		RequirementTemplate(
			req_key="sleep_quick_start",
			description="The system shall provide a one-step sleep quick start action that begins a sleep session immediately.",
			acceptance_criteria=(
				"Given the user opens the app before bedtime, When the user selects Sleep Quick Start, "
				"Then playback shall begin within a short startup time and without unnecessary intermediate prompts."
			),
		),
		RequirementTemplate(
			req_key="sleep_filtering",
			description="The system shall allow filtering sleep content by narrator, duration, and content type.",
			acceptance_criteria=(
				"Given the user applies sleep filters, When filtered results are displayed, "
				"Then returned items shall match selected filter values with high relevance."
			),
		),
		RequirementTemplate(
			req_key="short_sleep_collection",
			description="The system shall provide a dedicated short sleep collection for sessions with brief durations.",
			acceptance_criteria=(
				"Given the user opens the short sleep collection, When content is listed, "
				"Then most sessions shall fall within short-duration ranges suitable for quick bedtime use."
			),
		),
	],
	"G2": [
		RequirementTemplate(
			req_key="mood_based_recommendations",
			description="The system shall recommend meditation sessions using user-selected mood and available time.",
			acceptance_criteria=(
				"Given the user selects a mood and time budget, When recommendations are generated, "
				"Then the system shall present multiple sessions aligned with both inputs."
			),
		),
		RequirementTemplate(
			req_key="favorites_reuse",
			description="The system shall allow users to save meditation sessions and replay them from a Favorites view.",
			acceptance_criteria=(
				"Given a session is marked as favorite, When the user opens Favorites, "
				"Then the saved session shall be visible and directly playable."
			),
		),
	],
	"G3": [
		RequirementTemplate(
			req_key="billing_transparency",
			description="The system shall display pricing, trial terms, and renewal timing before subscription confirmation.",
			acceptance_criteria=(
				"Given the user reaches subscription confirmation, When billing details are shown, "
				"Then price, trial terms, and renewal information shall be clearly visible before final confirmation."
			),
		),
		RequirementTemplate(
			req_key="in_app_cancellation",
			description="The system shall provide an in-app cancellation path with explicit completion confirmation.",
			acceptance_criteria=(
				"Given the user initiates cancellation, When cancellation is completed, "
				"Then the system shall show clear confirmation and updated subscription status."
			),
		),
		RequirementTemplate(
			req_key="billing_history",
			description="The system shall provide billing history entries with date, amount, and charge type details.",
			acceptance_criteria=(
				"Given the user opens billing history, When entries are displayed, "
				"Then each entry shall include enough detail to identify charge origin and timing."
			),
		),
	],
	"G4": [
		RequirementTemplate(
			req_key="audio_controls",
			description="The system shall provide playback controls for narrator volume, background audio volume, and speed.",
			acceptance_criteria=(
				"Given guided content is playing, When the user adjusts audio controls, "
				"Then playback output shall reflect the new settings with minimal delay."
			),
		),
		RequirementTemplate(
			req_key="narrator_discovery",
			description="The system shall support narrator-based search and a narrator page listing related sessions.",
			acceptance_criteria=(
				"Given the user searches by narrator name, When results are shown, "
				"Then the user shall be able to open a narrator page and browse related content in one place."
			),
		),
	],
	"G5": [
		RequirementTemplate(
			req_key="post_update_stability",
			description="The system shall preserve startup, login, search, and playback reliability after application updates.",
			acceptance_criteria=(
				"Given a new app version is installed, When core workflows are executed, "
				"Then startup, login, search, and playback shall complete without blocking failures."
			),
		),
		RequirementTemplate(
			req_key="search_relevance",
			description="The system shall return relevant search results with category labels and filter refinement support.",
			acceptance_criteria=(
				"Given the user submits a keyword query, When search results load, "
				"Then results shall be relevant and include category labels and functional filters."
			),
		),
	],
}


def load_personas(path: Path) -> List[dict]:
	with path.open("r", encoding="utf-8") as f:
		payload = json.load(f)
	personas = payload.get("personas", [])
	if not personas:
		raise ValueError("No personas found in personas_auto.json")
	return personas


def persona_label(persona: dict) -> str:
	return f"{persona.get('id', 'P?')} - {persona.get('name', 'Unknown Persona')}"


def generate_requirements(personas: List[dict]) -> List[dict]:
	requirements: List[dict] = []
	req_counter = 1

	for persona in personas:
		group_id = persona.get("derived_from_group", "")
		templates = TEMPLATES_BY_GROUP.get(group_id, [])
		for template in templates:
			requirements.append(
				{
					"requirement_id": f"FR_auto_{req_counter:02d}",
					"description": template.description,
					"source_persona": persona_label(persona),
					"traceability": f"Derived from review group {group_id}",
					"acceptance_criteria": template.acceptance_criteria,
				}
			)
			req_counter += 1

	if not requirements:
		raise ValueError("No requirements generated. Check persona group mappings.")

	return requirements


def format_markdown(requirements: List[dict]) -> str:
	blocks: List[str] = []
	for req in requirements:
		blocks.append(
			"\n".join(
				[
					f"# Requirement ID: {req['requirement_id']}",
					f"- Description: [{req['description']}]",
					f"- Source Persona: [{req['source_persona']}]",
					f"- Traceability: [{req['traceability']}]",
					f"- Acceptance Criteria: [{req['acceptance_criteria']}]",
				]
			)
		)

	return "\n\n\n".join(blocks) + "\n"


def main() -> None:
	if not INPUT_PERSONAS_PATH.exists():
		raise FileNotFoundError(f"Missing input personas file: {INPUT_PERSONAS_PATH}")

	personas = load_personas(INPUT_PERSONAS_PATH)
	requirements = generate_requirements(personas)
	markdown = format_markdown(requirements)

	OUTPUT_SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
	with OUTPUT_SPEC_PATH.open("w", encoding="utf-8") as f:
		f.write(markdown)

	print(f"Wrote: {OUTPUT_SPEC_PATH}")
	print(f"Generated requirements: {len(requirements)}")


if __name__ == "__main__":
	main()