"""Validate repository structure and required artifact completeness.

Through this validation script, all required folders and essential files are checked
for presence and basic integrity. The script reports clearly whether the repository
is properly structured and ready for pipeline execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parents[1]


# Required folder structure
REQUIRED_FOLDERS = [
    "data",
    "personas",
    "spec",
    "tests",
    "metrics",
    "prompts",
    "src",
]

# Required files for each pipeline variant
REQUIRED_FILES = {
    "automated": {
        "data/reviews_clean.jsonl": "Cleaned reviews dataset",
        "data/review_groups_auto.json": "Automated review groupings",
        "personas/personas_auto.json": "Automated personas",
        "spec/spec_auto.md": "Automated specifications",
        "tests/tests_auto.json": "Automated tests",
        "metrics/metrics_auto.json": "Automated metrics",
    },
    "manual": {
        "data/review_groups_manual.json": "Manual review groupings",
        "personas/personas_manual.json": "Manual personas",
        "spec/spec_manual.md": "Manual specifications",
        "tests/tests_manual.json": "Manual tests",
        "metrics/metrics_manual.json": "Manual metrics",
    },
    "hybrid": {
        "data/review_groups_hybrid.json": "Hybrid review groupings",
        "personas/personas_hybrid.json": "Hybrid personas",
        "spec/spec_hybrid.md": "Hybrid specifications",
        "tests/tests_hybrid.json": "Hybrid tests",
        "metrics/metrics_hybrid.json": "Hybrid metrics",
    },
    "summary": {
        "metrics/metrics_summary.json": "Pipeline metrics comparison",
    },
}


def check_folder_structure() -> Tuple[bool, List[str]]:
    """Check that all required folders exist.
    
    By examining the directory tree, this function verifies that the repository
    has been initialized with proper folder organization for all pipeline artifacts.
    """
    missing = []
    for folder in REQUIRED_FOLDERS:
        folder_path = BASE_DIR / folder
        if not folder_path.is_dir():
            missing.append(folder)
    
    return (len(missing) == 0, missing)


def check_files(pipeline_names: list[str] | None = None) -> Tuple[bool, Dict[str, List[str]]]:
    """Check that all required files exist for specified pipelines.
    
    For each pipeline variant, this function verifies file presence and reports
    which files are missing. If no pipelines are specified, all variants are checked.
    """
    if pipeline_names is None:
        pipeline_names = ["automated", "manual", "hybrid", "summary"]
    
    all_missing = {}
    
    for pipeline in pipeline_names:
        if pipeline not in REQUIRED_FILES:
            continue
        
        missing = []
        for file_path, description in REQUIRED_FILES[pipeline].items():
            full_path = BASE_DIR / file_path
            if not full_path.is_file():
                missing.append(f"{file_path} ({description})")
        
        if missing:
            all_missing[pipeline] = missing
    
    return (len(all_missing) == 0, all_missing)


def check_file_validity() -> Tuple[bool, List[str]]:
    """Check that JSON and JSONL files are syntactically valid.
    
    By parsing JSON content, this validation ensures that artifact files are
    well-formed and not corrupted through the pipeline execution.
    """
    issues = []
    json_files = [
        BASE_DIR / "data" / "reviews_clean.jsonl",
        BASE_DIR / "data" / "review_groups_auto.json",
        BASE_DIR / "data" / "review_groups_manual.json",
        BASE_DIR / "data" / "review_groups_hybrid.json",
        BASE_DIR / "personas" / "personas_auto.json",
        BASE_DIR / "personas" / "personas_manual.json",
        BASE_DIR / "personas" / "personas_hybrid.json",
        BASE_DIR / "tests" / "tests_auto.json",
        BASE_DIR / "tests" / "tests_manual.json",
        BASE_DIR / "tests" / "tests_hybrid.json",
        BASE_DIR / "metrics" / "metrics_auto.json",
        BASE_DIR / "metrics" / "metrics_manual.json",
        BASE_DIR / "metrics" / "metrics_hybrid.json",
        BASE_DIR / "metrics" / "metrics_summary.json",
    ]
    
    for file_path in json_files:
        if not file_path.exists():
            continue
        
        try:
            if file_path.suffix == ".jsonl":
                with file_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            json.loads(line)
            else:
                # Use utf-8-sig to handle BOM
                with file_path.open("r", encoding="utf-8-sig") as f:
                    json.load(f)
        except json.JSONDecodeError as e:
            issues.append(f"{file_path.name}: {e}")
        except Exception as e:
            issues.append(f"{file_path.name}: {e}")
    
    return (len(issues) == 0, issues)


def main() -> None:
    """Execute full repository validation and report results."""
    print("Checking repository structure...")
    
    # Check folder structure
    folders_ok, missing_folders = check_folder_structure()
    if folders_ok:
        for folder in REQUIRED_FOLDERS:
            print(f"✓ {folder}/ exists")
    else:
        print("✗ Missing folders:")
        for folder in missing_folders:
            print(f"  - {folder}/")
    
    print()
    
    # Check files for all pipelines
    files_ok, missing_files = check_files()
    
    for pipeline in ["automated", "manual", "hybrid", "summary"]:
        print(f"{pipeline.upper()} PIPELINE:")
        if pipeline in missing_files:
            for file_desc in missing_files[pipeline]:
                print(f"  ✗ {file_desc}")
        else:
            for file_path in REQUIRED_FILES.get(pipeline, {}).keys():
                file_name = file_path.split("/")[-1]
                print(f"  ✓ {file_name} found")
        print()
    
    # Check JSON validity
    json_ok, json_issues = check_file_validity()
    if not json_ok:
        print("JSON/JSONL VALIDITY ISSUES:")
        for issue in json_issues:
            print(f"  ✗ {issue}")
        print()
    
    # Final report
    print("=" * 70)
    if folders_ok and files_ok and json_ok:
        print("RESULT: Repository validation complete - all required artifacts present")
        print("=" * 70)
        return
    
    print("RESULT: Repository validation FAILED - missing or invalid artifacts")
    if missing_folders:
        print(f"  - {len(missing_folders)} folder(s) missing")
    if missing_files:
        total_missing = sum(len(v) for v in missing_files.values())
        print(f"  - {total_missing} file(s) missing across pipelines")
    if json_issues:
        print(f"  - {len(json_issues)} JSON/JSONL validity issue(s)")
    print("=" * 70)


if __name__ == "__main__":
    main()