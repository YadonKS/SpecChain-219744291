"""Collect reviews for a Google Play app and save them as JSONL.

Default target is 2,000 reviews (clamped to 1,000..5,000). If the app has fewer
than 1,000 reviews available, the script collects all available reviews.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from google_play_scraper import app as fetch_app
from google_play_scraper import reviews


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_PATH = DATA_DIR / "reviews_raw.jsonl"
METADATA_PATH = DATA_DIR / "dataset_metadata.json"

APP_ID = os.getenv("APP_ID", "com.calm.android")
LANG = os.getenv("APP_LANG", "en")
COUNTRY = os.getenv("APP_COUNTRY", "ca")
MIN_TARGET = 1000
MAX_TARGET = 5000
DEFAULT_TARGET = 2000


def _safe_int(value: Any, fallback: int) -> int:
	try:
		return int(value)
	except (TypeError, ValueError):
		return fallback


def _resolve_target() -> int:
	requested = _safe_int(os.getenv("REVIEW_TARGET"), DEFAULT_TARGET)
	return max(MIN_TARGET, min(MAX_TARGET, requested))


def _to_iso(value: Any) -> Optional[str]:
	if value is None:
		return None
	if hasattr(value, "isoformat"):
		return value.isoformat()
	return str(value)


def _normalize_review(raw: Dict[str, Any]) -> Dict[str, Any]:
	return {
		"reviewId": raw.get("reviewId"),
		"userName": raw.get("userName"),
		"score": raw.get("score"),
		"content": raw.get("content"),
		"at": _to_iso(raw.get("at")),
		"thumbsUpCount": raw.get("thumbsUpCount"),
		"reviewCreatedVersion": raw.get("reviewCreatedVersion"),
		"replyContent": raw.get("replyContent"),
		"repliedAt": _to_iso(raw.get("repliedAt")),
		"appId": APP_ID,
		"lang": LANG,
		"country": COUNTRY,
	}


def collect_reviews() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
	app_details = fetch_app(APP_ID, lang=LANG, country=COUNTRY)
	app_name = app_details.get("title") or APP_ID
	estimated_total = app_details.get("reviews")
	target = _resolve_target()

	# If we know there are fewer than 1,000 reviews, collect all available.
	if isinstance(estimated_total, int) and estimated_total < MIN_TARGET:
		desired = MAX_TARGET
	else:
		desired = target

	all_reviews: List[Dict[str, Any]] = []
	seen_ids = set()
	token = None

	while len(all_reviews) < desired:
		batch_size = min(200, desired - len(all_reviews))
		batch, token = reviews(
			APP_ID,
			lang=LANG,
			country=COUNTRY,
			count=batch_size,
			continuation_token=token,
		)

		if not batch:
			break

		for item in batch:
			normalized = _normalize_review(item)
			rid = normalized.get("reviewId")
			if rid and rid in seen_ids:
				continue
			if rid:
				seen_ids.add(rid)
			all_reviews.append(normalized)

		if token is None:
			break

	collected_at = datetime.now(timezone.utc).isoformat()
	meta = {
		"app_name": app_name,
		"app_id": APP_ID,
		"dataset_size": len(all_reviews),
		"collection_method": "google-play-scraper pagination via Google Play public listing",
		"collection_details": {
			"lang": LANG,
			"country": COUNTRY,
			"requested_target": target,
			"effective_target": desired,
			"minimum_requirement": MIN_TARGET,
			"maximum_requirement": MAX_TARGET,
			"estimated_total_reviews": estimated_total,
			"collected_at_utc": collected_at,
		},
		"cleaning_decisions": {},
	}
	return all_reviews, meta


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8") as handle:
		for row in rows:
			handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
	rows, metadata = collect_reviews()
	write_jsonl(RAW_PATH, rows)
	with METADATA_PATH.open("w", encoding="utf-8") as handle:
		json.dump(metadata, handle, indent=2, ensure_ascii=False)

	print(f"Collected {len(rows)} reviews for {metadata['app_name']} ({APP_ID}).")
	print(f"Saved raw dataset to: {RAW_PATH}")
	print(f"Saved metadata to: {METADATA_PATH}")


if __name__ == "__main__":
	main()