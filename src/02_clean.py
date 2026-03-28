"""Clean raw review data and save a normalized dataset."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import nltk
from num2words import num2words
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_PATH = DATA_DIR / "reviews_raw.jsonl"
CLEAN_PATH = DATA_DIR / "reviews_clean.jsonl"
METADATA_PATH = DATA_DIR / "dataset_metadata.json"
MIN_TOKENS = 3

EMOJI_PATTERN = re.compile(
	"["
	"\U0001F1E0-\U0001F1FF"  # flags
	"\U0001F300-\U0001F5FF"  # symbols & pictographs
	"\U0001F600-\U0001F64F"  # emoticons
	"\U0001F680-\U0001F6FF"  # transport & map
	"\U0001F700-\U0001F77F"  # alchemical
	"\U0001F780-\U0001F7FF"  # geometric extended
	"\U0001F800-\U0001F8FF"  # supplemental arrows-c
	"\U0001F900-\U0001F9FF"  # supplemental symbols
	"\U0001FA00-\U0001FA6F"  # chess, symbols, etc.
	"\U0001FA70-\U0001FAFF"  # symbols and pictographs ext-a
	"]+",
	flags=re.UNICODE,
)
NON_ALPHA_PATTERN = re.compile(r"[^a-z\s]+")
WHITESPACE_PATTERN = re.compile(r"\s+")
NUMBER_PATTERN = re.compile(r"\d+")


def _ensure_nltk_resource(resource: str, path: str) -> None:
	try:
		nltk.data.find(path)
	except LookupError:
		nltk.download(resource, quiet=True)


def setup_nlp() -> tuple[set[str], WordNetLemmatizer]:
	_ensure_nltk_resource("stopwords", "corpora/stopwords")
	_ensure_nltk_resource("wordnet", "corpora/wordnet")
	_ensure_nltk_resource("omw-1.4", "corpora/omw-1.4")
	return set(stopwords.words("english")), WordNetLemmatizer()


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
	rows: List[Dict[str, Any]] = []
	if not path.exists():
		return rows
	with path.open("r", encoding="utf-8") as handle:
		for line in handle:
			line = line.strip()
			if not line:
				continue
			rows.append(json.loads(line))
	return rows


def write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8") as handle:
		for row in rows:
			handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _numbers_to_text(text: str) -> str:
	def replace(match: re.Match[str]) -> str:
		try:
			return " " + num2words(int(match.group(0))) + " "
		except Exception:
			return " "

	return NUMBER_PATTERN.sub(replace, text)


def clean_text(text: str, stop_words: set[str], lemmatizer: WordNetLemmatizer) -> str:
	text = text.strip()
	text = EMOJI_PATTERN.sub(" ", text)
	text = _numbers_to_text(text)
	text = text.lower()
	text = NON_ALPHA_PATTERN.sub(" ", text)
	text = WHITESPACE_PATTERN.sub(" ", text).strip()

	tokens = []
	for token in text.split(" "):
		if not token or token in stop_words:
			continue
		lemma = lemmatizer.lemmatize(token)
		if lemma and lemma not in stop_words:
			tokens.append(lemma)

	return " ".join(tokens)


def _pick_text(review: Dict[str, Any]) -> str:
	for key in ("content", "text", "review", "review_text"):
		value = review.get(key)
		if isinstance(value, str):
			return value
	return ""


def _load_metadata(path: Path) -> Dict[str, Any]:
	if not path.exists():
		return {}
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def _write_metadata(path: Path, metadata: Dict[str, Any]) -> None:
	with path.open("w", encoding="utf-8") as handle:
		json.dump(metadata, handle, indent=2, ensure_ascii=False)


def main() -> None:
	raw_rows = read_jsonl(RAW_PATH)
	stop_words, lemmatizer = setup_nlp()

	cleaned_rows: List[Dict[str, Any]] = []
	seen_review_ids = set()
	seen_clean_text = set()

	for review in raw_rows:
		review_id = review.get("reviewId")
		if review_id and review_id in seen_review_ids:
			continue

		raw_text = _pick_text(review)
		if not raw_text or not raw_text.strip():
			continue

		cleaned_text = clean_text(raw_text, stop_words, lemmatizer)
		if not cleaned_text:
			continue

		token_count = len(cleaned_text.split())
		if token_count < MIN_TOKENS:
			continue

		if cleaned_text in seen_clean_text:
			continue

		if review_id:
			seen_review_ids.add(review_id)
		seen_clean_text.add(cleaned_text)

		cleaned_rows.append(
			{
				"reviewId": review_id,
				"appId": review.get("appId"),
				"score": review.get("score"),
				"at": review.get("at"),
				"text": cleaned_text,
				"raw_text": raw_text,
			}
		)

	write_jsonl(CLEAN_PATH, cleaned_rows)

	metadata = _load_metadata(METADATA_PATH)
	metadata.setdefault("app_name", "Calm")
	metadata.setdefault("app_id", "com.calm.android")
	metadata["dataset_size"] = len(cleaned_rows)
	metadata["dataset_size_raw"] = len(raw_rows)
	metadata["dataset_size_clean"] = len(cleaned_rows)
	metadata["collection_method"] = metadata.get(
		"collection_method",
		"google-play-scraper pagination via Google Play public listing",
	)
	metadata["cleaning_decisions"] = {
		"remove_duplicates": True,
		"remove_empty_entries": True,
		"remove_extremely_short_reviews": True,
		"minimum_tokens_after_cleaning": MIN_TOKENS,
		"remove_punctuation": True,
		"remove_special_characters": True,
		"remove_emojis": True,
		"convert_numbers_to_text": True,
		"normalize_whitespace": True,
		"lowercase": True,
		"remove_stop_words": True,
		"lemmatize": True,
	}
	_write_metadata(METADATA_PATH, metadata)

	print(f"Loaded raw reviews: {len(raw_rows)}")
	print(f"Saved cleaned reviews: {len(cleaned_rows)}")
	print(f"Cleaned dataset path: {CLEAN_PATH}")
	print(f"Metadata path: {METADATA_PATH}")


if __name__ == "__main__":
	main()