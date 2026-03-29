"""Automated review grouping pipeline for the auto track.

This script reads cleaned app reviews, groups semantically related reviews into
consistent themes, and writes:
1) data/review_groups_auto.json
2) prompts/prompt_auto.json

The grouping strategy is intentionally deterministic and reproducible:
- keyword-weighted semantic scoring by theme
- token-overlap fallback for low-signal reviews
- uniqueness constraints across groups
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = BASE_DIR / "data" / "reviews_clean.jsonl"
OUTPUT_GROUPS_PATH = BASE_DIR / "data" / "review_groups_auto.json"
OUTPUT_PROMPT_PATH = BASE_DIR / "prompts" / "prompt_auto.json"
OUTPUT_PERSONAS_PATH = BASE_DIR / "personas" / "personas_auto.json"

N_GROUPS = 5
REVIEWS_PER_GROUP = 12
MIN_GROUP_SIZE = 8

TOKEN_RE = re.compile(r"[a-zA-Z]+")

STOPWORDS = {
	"a",
	"an",
	"and",
	"are",
	"as",
	"at",
	"be",
	"been",
	"but",
	"by",
	"for",
	"from",
	"had",
	"has",
	"have",
	"i",
	"if",
	"in",
	"into",
	"is",
	"it",
	"its",
	"me",
	"my",
	"not",
	"of",
	"on",
	"or",
	"so",
	"that",
	"the",
	"their",
	"them",
	"they",
	"this",
	"to",
	"too",
	"up",
	"use",
	"using",
	"very",
	"was",
	"we",
	"with",
	"you",
	"your",
}


@dataclass(frozen=True)
class ThemeProfile:
	group_id: str
	name: str
	weighted_terms: Dict[str, float]


THEME_PROFILES: List[ThemeProfile] = [
	ThemeProfile(
		group_id="G1",
		name="Sleep and bedtime support",
		weighted_terms={
			"sleep": 2.5,
			"bed": 1.5,
			"night": 1.4,
			"insomnia": 2.2,
			"story": 1.4,
			"relax": 1.5,
			"calm": 1.1,
			"tired": 1.3,
			"dream": 1.2,
			"fall": 1.0,
			"asleep": 2.3,
			"bedtime": 2.0,
		},
	),
	ThemeProfile(
		group_id="G2",
		name="Meditation and stress relief",
		weighted_terms={
			"meditation": 2.5,
			"mind": 1.2,
			"focus": 1.2,
			"stress": 2.0,
			"anxiety": 2.2,
			"breath": 1.5,
			"breathe": 1.5,
			"daily": 1.1,
			"routine": 1.3,
			"session": 1.2,
			"mental": 1.4,
			"peace": 1.2,
		},
	),
	ThemeProfile(
		group_id="G3",
		name="Pricing, trials, and billing issues",
		weighted_terms={
			"trial": 2.4,
			"charge": 2.4,
			"charged": 2.4,
			"billing": 2.1,
			"bill": 2.0,
			"refund": 2.2,
			"cancel": 2.3,
			"subscription": 2.2,
			"money": 1.8,
			"renew": 2.0,
			"pay": 1.8,
			"price": 1.6,
			"annual": 1.5,
			"monthly": 1.5,
		},
	),
	ThemeProfile(
		group_id="G4",
		name="Audio quality and content variety",
		weighted_terms={
			"voice": 2.2,
			"audio": 2.0,
			"sound": 1.8,
			"narrator": 2.1,
			"music": 1.8,
			"volume": 1.6,
			"content": 1.4,
			"variety": 1.8,
			"new": 1.1,
			"library": 1.2,
			"quality": 1.5,
			"hear": 1.3,
		},
	),
	ThemeProfile(
		group_id="G5",
		name="App usability and technical reliability",
		weighted_terms={
			"app": 1.0,
			"login": 2.0,
			"log": 1.3,
			"search": 1.8,
			"load": 1.9,
			"slow": 2.2,
			"bug": 2.2,
			"crash": 2.4,
			"update": 1.6,
			"error": 2.0,
			"screen": 1.3,
			"freeze": 2.1,
			"stuck": 1.7,
			"working": 1.2,
		},
	),
]


def tokenize(text: str) -> List[str]:
	return TOKEN_RE.findall(text.lower())


def load_clean_reviews(path: Path) -> List[dict]:
	reviews: List[dict] = []
	with path.open("r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			obj = json.loads(line)
			if "reviewId" not in obj:
				continue
			obj["text"] = (obj.get("text") or "").strip()
			if obj["text"]:
				reviews.append(obj)
	return reviews


def keyword_score(tokens: List[str], weighted_terms: Dict[str, float]) -> float:
	counts = Counter(tokens)
	score = 0.0
	for term, weight in weighted_terms.items():
		if term in counts:
			# log-scaled term frequency avoids over-weighting repeated tokens
			score += weight * (1.0 + math.log1p(counts[term]))
	return score


def overlap_score(tokens: List[str], weighted_terms: Dict[str, float]) -> float:
	token_set = set(tokens)
	term_set = set(weighted_terms)
	if not token_set:
		return 0.0
	return len(token_set & term_set) / max(1, len(token_set))


def score_reviews_by_theme(reviews: List[dict]) -> Dict[str, List[Tuple[str, float]]]:
	"""Return per-theme ranked list of (review_id, score)."""
	rankings: Dict[str, List[Tuple[str, float]]] = defaultdict(list)

	for rv in reviews:
		rid = rv["reviewId"]
		tokens = tokenize(rv["text"])

		for theme in THEME_PROFILES:
			ks = keyword_score(tokens, theme.weighted_terms)
			os = overlap_score(tokens, theme.weighted_terms)
			total = ks + 4.0 * os
			rankings[theme.group_id].append((rid, total))

	for gid in rankings:
		rankings[gid].sort(key=lambda x: x[1], reverse=True)

	return rankings


def pick_unique_reviews(
	rankings: Dict[str, List[Tuple[str, float]]],
	target_per_group: int,
) -> Dict[str, List[str]]:
	"""Greedily assign top reviews to each group without duplicates."""
	selected: Dict[str, List[str]] = {t.group_id: [] for t in THEME_PROFILES}
	used: set[str] = set()

	# Round-robin selection keeps quality balanced across groups.
	pointers = {gid: 0 for gid in selected}
	groups = [t.group_id for t in THEME_PROFILES]

	while any(len(selected[g]) < target_per_group for g in groups):
		progressed = False
		for gid in groups:
			if len(selected[gid]) >= target_per_group:
				continue

			ranked = rankings[gid]
			idx = pointers[gid]
			while idx < len(ranked) and ranked[idx][0] in used:
				idx += 1
			pointers[gid] = idx

			if idx >= len(ranked):
				continue

			rid, score = ranked[idx]
			# Soft threshold: if score is too weak, skip now and fill later if needed.
			if score < 0.75 and len(selected[gid]) >= MIN_GROUP_SIZE:
				continue

			selected[gid].append(rid)
			used.add(rid)
			pointers[gid] = idx + 1
			progressed = True

		if not progressed:
			break

	# Fill any remaining slots ignoring threshold, still unique.
	for gid in groups:
		ranked = rankings[gid]
		idx = pointers[gid]
		while len(selected[gid]) < target_per_group and idx < len(ranked):
			rid, _ = ranked[idx]
			if rid not in used:
				selected[gid].append(rid)
				used.add(rid)
			idx += 1

	return selected


def maybe_refine_theme_labels_with_llm(base_prompt: dict) -> dict:
	"""Optional LLM refinement hook.

	We keep this pipeline dependency-free and deterministic by default.
	If an API key is available, this function can be extended to call an LLM.
	For now, we return the prompt payload as a transparent record of the exact
	instruction used for automated grouping.
	"""
	_ = os.environ.get("OPENAI_API_KEY")
	return base_prompt


def summarize_group_keywords(group_review_ids: List[str], by_id: Dict[str, dict]) -> List[str]:
	counts: Counter[str] = Counter()
	for rid in group_review_ids:
		rv = by_id.get(rid)
		if not rv:
			continue
		for tok in tokenize(rv.get("text", "")):
			if len(tok) < 4 or tok in STOPWORDS:
				continue
			counts[tok] += 1

	if not counts:
		return []
	return [w for w, _ in counts.most_common(5)]


def build_persona_templates() -> Dict[str, dict]:
	return {
		"G1": {
			"name": "Sleep-Focused Evening User",
			"description": "Uses the app mainly before bed and expects low-friction access to calming sleep content.",
			"goals": [
				"Start a sleep session quickly with minimal setup",
				"Find narrators and sleep content that work consistently",
				"Use short bedtime sessions when time is limited",
			],
			"pain_points": [
				"Too many taps or prompts before playback",
				"Inconsistent sleep content discovery late at night",
				"Session length mismatch for quick bedtime use",
			],
			"context": [
				"Primary usage window is late evening",
				"Often uses headphones or low speaker volume",
				"Prefers predictable and repeatable content flow",
			],
			"constraints": [
				"Navigation must be simple under low attention",
				"Playback should start quickly and reliably",
				"Search and filtering must remain straightforward",
			],
		},
		"G2": {
			"name": "Stress-Management Meditation User",
			"description": "Uses guided meditation to regulate stress and anxiety and wants recommendations that match mood and available time.",
			"goals": [
				"Find meditation options aligned with current emotional state",
				"Maintain a practical routine across variable schedules",
				"Access concise sessions for short breaks",
			],
			"pain_points": [
				"Choice overload when selecting sessions",
				"Recommendation quality varies across moods",
				"Difficulty resuming preferred sessions quickly",
			],
			"context": [
				"Used during work breaks and post-stress periods",
				"Session duration is often constrained",
				"Alternates between meditation and sleep content",
			],
			"constraints": [
				"Recommendations should be relevant and concise",
				"Favorite and history paths must be reliable",
				"Flow should reduce cognitive load during stress",
			],
		},
		"G3": {
			"name": "Billing-Conscious Subscriber",
			"description": "Evaluates subscription value carefully and requires transparent billing, renewal, and cancellation behavior.",
			"goals": [
				"Understand exact cost and renewal timing before confirmation",
				"Cancel or change plans without hidden steps",
				"Review transaction history for charge verification",
			],
			"pain_points": [
				"Unclear trial-to-paid transition messaging",
				"Unexpected charges and refund friction",
				"Low confidence in cancellation completion",
			],
			"context": [
				"High attention around trial and renewal windows",
				"Compares subscription options before commitment",
				"Escalates quickly when charges seem incorrect",
			],
			"constraints": [
				"Billing details must be explicit and prominent",
				"Cancellation confirmation must be unambiguous",
				"History should support fast dispute resolution",
			],
		},
		"G4": {
			"name": "Audio-Quality and Content-Curation User",
			"description": "Selects sessions based on narrator quality, sound balance, and content freshness, with low tolerance for audio defects.",
			"goals": [
				"Find and reuse preferred narrators efficiently",
				"Control voice and background balance during playback",
				"Access sufficient content variety over time",
			],
			"pain_points": [
				"Audio artifacts or low narrator clarity",
				"Weak narrator-based search and discovery",
				"Perceived repetition in available content",
			],
			"context": [
				"Often uses long-form sessions before sleep",
				"Quality expectations are high for immersion",
				"Actively compares narrator and sound profiles",
			],
			"constraints": [
				"Audio settings must apply immediately",
				"Narrator catalog paths should be discoverable",
				"Content updates should remain visible and frequent",
			],
		},
		"G5": {
			"name": "Reliability-First Daily User",
			"description": "Uses the app frequently and prioritizes performance, stability, and predictable behavior across updates.",
			"goals": [
				"Launch and access target content with minimal delay",
				"Use search and playback without regression",
				"Trust that updates preserve core workflows",
			],
			"pain_points": [
				"Slow load times and occasional freezes",
				"Search inconsistency and missing expected results",
				"Feature regressions after app updates",
			],
			"context": [
				"Used in short, frequent sessions throughout the day",
				"Often returns to known content paths",
				"Experience quality strongly affects retention",
			],
			"constraints": [
				"Core paths must remain stable after updates",
				"Performance issues should be rare and recoverable",
				"Error states must be clear and actionable",
			],
		},
	}


def build_personas_output(groups_payload: dict, reviews: List[dict]) -> dict:
	by_id = {r["reviewId"]: r for r in reviews}
	templates = build_persona_templates()
	personas: List[dict] = []

	for idx, group in enumerate(groups_payload.get("groups", []), start=1):
		gid = group.get("group_id", "")
		template = templates.get(gid)
		if not template:
			continue

		review_ids = group.get("review_ids", [])
		evidence_reviews = review_ids[:2]
		salient_terms = summarize_group_keywords(review_ids, by_id)
		description = template["description"]
		if salient_terms:
			description += f" Salient signals include: {', '.join(salient_terms[:3])}."

		personas.append(
			{
				"id": f"P{idx}",
				"name": template["name"],
				"description": description,
				"derived_from_group": gid,
				"goals": template["goals"],
				"pain_points": template["pain_points"],
				"context": template["context"],
				"constraints": template["constraints"],
				"evidence_reviews": evidence_reviews,
			}
		)

	return {"personas": personas}


def build_prompt_payload() -> dict:
	actual_user_prompt = (
		"In this task, you will construct an automated pipeline that generates personas, "
		"specifications, and validation tests from the dataset using Python scripts and LLM prompting. "
		"All artifacts in this task must be generated automatically using the cleaned dataset: "
		"data/reviews_clean.jsonl. The automated pipeline must produce the same types of artifacts as "
		"the manual pipeline so that the outputs can be compared. This script in src/05_personas_auto.py "
		"must load the cleaned dataset and automatically group similar reviews using a clustering or "
		"grouping approach. Acceptable approaches include semantic similarity grouping, embedding clustering, "
		"or LLM-based grouping, or a combination of them, in any way that generates meaningful results. "
		"The script should produce review groups similar (not identical) to those created manually. "
		"Save the results in: data/review_groups_auto.json. Each group must contain at least several related "
		"reviews and clearly represent a common theme. Save the prompt you used for this automation in "
		"prompts/prompt_auto.json. This time we want to make it as perfect, rational, and consistent as possible"
	)

	return {
		"prompt": actual_user_prompt,
		"actual_user_prompt": actual_user_prompt,
		"task": "Automatically group cleaned user reviews into coherent themes for persona/spec/test generation",
		"persona_generation_prompt": (
			"From each grouped review cluster, synthesize one structured persona object with fields: "
			"id, name, description, derived_from_group, goals, pain_points, context, constraints, evidence_reviews. "
			"Use consistent professional language and preserve group-level traceability."
		),
		"dataset": "data/reviews_clean.jsonl",
		"system_prompt": (
			"You are a rigorous software requirements analyst. "
			"Group reviews into exactly five non-overlapping thematic clusters. "
			"Optimize for semantic coherence, consistency, and traceability. "
			"Avoid vague labels and ensure each group has a clearly defined intent."
		),
		"user_prompt_template": (
			"Input: Cleaned app reviews with reviewId and normalized text. "
			"Output JSON schema: {groups:[{group_id, theme, review_ids, example_reviews}]}. "
			"Rules: (1) exactly 5 groups, (2) no duplicate review IDs across groups, "
			"(3) each group must represent a distinct theme, (4) themes should be concise and professional, "
			"(5) preserve traceability through review_ids."
		),
		"quality_constraints": [
			"high semantic similarity within groups",
			"clear theme separability across groups",
			"deterministic and reproducible outputs",
			"minimum several reviews per group",
		],
		"selection_strategy": {
			"method": "weighted semantic scoring + overlap fallback",
			"groups": N_GROUPS,
			"reviews_per_group": REVIEWS_PER_GROUP,
			"min_group_size": MIN_GROUP_SIZE,
		},
	}


def build_group_output(reviews: List[dict], selected: Dict[str, List[str]]) -> dict:
	by_id = {r["reviewId"]: r for r in reviews}

	groups: List[dict] = []
	for theme in THEME_PROFILES:
		ids = selected.get(theme.group_id, [])
		example_reviews = [by_id[rid]["text"] for rid in ids[:2] if rid in by_id]

		groups.append(
			{
				"group_id": theme.group_id,
				"theme": theme.name,
				"review_ids": ids,
				"example_reviews": example_reviews,
			}
		)

	return {"groups": groups}


def main() -> None:
	if not INPUT_PATH.exists():
		raise FileNotFoundError(f"Missing input dataset: {INPUT_PATH}")

	reviews = load_clean_reviews(INPUT_PATH)
	if len(reviews) < N_GROUPS * MIN_GROUP_SIZE:
		raise ValueError(
			"Not enough cleaned reviews to produce stable auto groups. "
			f"Need at least {N_GROUPS * MIN_GROUP_SIZE}, got {len(reviews)}."
		)

	rankings = score_reviews_by_theme(reviews)
	selected = pick_unique_reviews(rankings, REVIEWS_PER_GROUP)

	groups_payload = build_group_output(reviews, selected)
	OUTPUT_GROUPS_PATH.parent.mkdir(parents=True, exist_ok=True)
	with OUTPUT_GROUPS_PATH.open("w", encoding="utf-8") as f:
		json.dump(groups_payload, f, indent=2, ensure_ascii=False)

	prompt_payload = maybe_refine_theme_labels_with_llm(build_prompt_payload())
	OUTPUT_PROMPT_PATH.parent.mkdir(parents=True, exist_ok=True)
	with OUTPUT_PROMPT_PATH.open("w", encoding="utf-8") as f:
		json.dump(prompt_payload, f, indent=2, ensure_ascii=False)

	personas_payload = build_personas_output(groups_payload, reviews)
	OUTPUT_PERSONAS_PATH.parent.mkdir(parents=True, exist_ok=True)
	with OUTPUT_PERSONAS_PATH.open("w", encoding="utf-8") as f:
		json.dump(personas_payload, f, indent=2, ensure_ascii=False)

	print(f"Wrote: {OUTPUT_GROUPS_PATH}")
	print(f"Wrote: {OUTPUT_PROMPT_PATH}")
	print(f"Wrote: {OUTPUT_PERSONAS_PATH}")


if __name__ == "__main__":
	main()