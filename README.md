# SpecChain Final Project

## Application Studied
This project studies the Google Play application **Calm - Sleep, Meditate, Relax** (`com.calm.android`).

## Dataset Summary
Through Google Play scraping and pagination, the dataset was collected and then cleaned before pipeline generation.

- Raw dataset file: `data/reviews_raw.jsonl`
- Raw dataset size: **2000 reviews**
- Cleaned dataset file: `data/reviews_clean.jsonl`
- Final cleaned dataset size: **1617 reviews**
- Collection metadata: `data/dataset_metadata.json`

Collection method used:
- `google-play-scraper` against public Google Play listings
- Language: English (`en`)
- Country: Canada (`ca`)

## Repository Structure
As the workflow moves from data to validation artifacts, the repository is organized by stage output.

- `data/` dataset files and review group files
- `personas/` manual, automated, and hybrid personas
- `spec/` generated requirement specifications
- `tests/` generated validation tests
- `metrics/` per-pipeline metrics and cross-pipeline summary
- `prompts/` generated prompt artifacts
- `reflection/` final comparative reflection
- `src/` executable Python scripts

## Exact Commands To Reproduce The Automated Pipeline
Before running scripts, open a terminal at the repository root.

1. Validate repository structure:
	- `python src/00_validate_repo.py`

2. Run full automated generation workflow:
	- `python src/run_all.py`

This command executes the automated stages in order:
- automated review grouping and persona generation (`src/05_personas_auto.py`)
- automated requirement generation (`src/06_spec_generate.py`)
- automated test generation (`src/07_tests_generate.py`)
- automated metrics computation (`src/08_metrics.py --pipeline automated`)

If `data/reviews_clean.jsonl` is missing, `run_all.py` first runs cleaning (`src/02_clean.py`).

## Outputs Produced By The Automated Workflow
After successful execution, the main generated artifacts are:

- `data/review_groups_auto.json`
- `personas/personas_auto.json`
- `spec/spec_auto.md`
- `tests/tests_auto.json`
- `metrics/metrics_auto.json`

For cross-pipeline comparison, see:
- `metrics/metrics_summary.json`

