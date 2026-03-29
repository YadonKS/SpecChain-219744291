"""Execute the automated SpecChain pipeline from start to finish.

This orchestration script runs all programmatically-generated workflow stages in sequence.
It processes cleaned reviews through grouping, persona generation, specification
creation, test generation, and metrics computation.

Workflow stages and outputs:
1. Clean raw reviews (optional; skipped if data/reviews_clean.jsonl exists)
   data/reviews_raw.jsonl → data/reviews_clean.jsonl
2. Generate automated review groups
   data/reviews_clean.jsonl → data/review_groups_auto.json
3. Generate personas from groups
   data/review_groups_auto.json → personas/personas_auto.json
4. Generate specifications from personas
   personas/personas_auto.json → spec/spec_auto.md
5. Generate tests from specifications
   spec/spec_auto.md → tests/tests_auto.json
6. Compute pipeline metrics
   all artifacts → metrics/metrics_auto.json

Manual and hybrid pipelines are created separately through deliberate human refinement
and are not included in this automated workflow.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


def run_stage(stage_num: int, script_name: str, description: str, args: list[str] | None = None) -> bool:
    """Execute a single pipeline stage and report status.
    
    Through this function, each stage runs with clear error handling. If execution
    succeeds, the script continues to the next stage; if it fails, the pipeline
    halts with a diagnostic message.
    """
    stage_script = BASE_DIR / "src" / script_name
    args = args or []
    
    print(f"\n[Stage {stage_num}] {description}")
    print(f"  Running: {script_name}")
    
    try:
        result = subprocess.run(
            ["python", str(stage_script)] + args,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            print(f"  ✗ FAILED: {script_name}")
            print(f"  Error output:\n{result.stderr}")
            return False
        
        print(f"  ✓ COMPLETED: {script_name}")
        return True
        
    except subprocess.TimeoutExpired:
        print(f"  ✗ TIMEOUT: {script_name} exceeded 300 seconds")
        return False
    except Exception as e:
        print(f"  ✗ ERROR: {script_name} - {e}")
        return False


def main() -> None:
    """Execute the full automated pipeline in order."""
    print("=" * 70)
    print("SpecChain Automated Pipeline Execution")
    print("=" * 70)
    
    # Skip cleaning if reviews_clean.jsonl already exists
    clean_data_path = BASE_DIR / "data" / "reviews_clean.jsonl"
    stages = [
        (1, "05_personas_auto.py", "Generate review groups and personas"),
        (2, "06_spec_generate.py", "Generate functional requirements"),
        (3, "07_tests_generate.py", "Generate validation tests"),
        (4, "08_metrics.py", "Compute pipeline metrics", ["--pipeline", "automated"]),
    ]
    
    if clean_data_path.exists():
        print("\nNote: data/reviews_clean.jsonl found - skipping data cleaning stage")
    else:
        stages.insert(0, (0, "02_clean.py", "Clean and normalize raw review dataset"))
    
    completed = 0
    failed_stage = None
    
    for stage_info in stages:
        stage_num = stage_info[0]
        script = stage_info[1]
        description = stage_info[2]
        args = stage_info[3] if len(stage_info) > 3 else None
        
        success = run_stage(stage_num, script, description, args)
        
        if success:
            completed += 1
        else:
            failed_stage = (stage_num, script)
            break
    
    print("\n" + "=" * 70)
    if failed_stage:
        stage_num, script = failed_stage
        print(f"Pipeline halted at stage {stage_num} ({script})")
        print(f"Total completed: {completed} of {len(stages)}")
        sys.exit(1)
    else:
        print("Pipeline execution complete: all stages succeeded")
        print(f"Total completed: {completed} of {len(stages)}")
        print("\nGenerated artifacts:")
        print("  - data/review_groups_auto.json")
        print("  - personas/personas_auto.json")
        print("  - spec/spec_auto.md")
        print("  - tests/tests_auto.json")
        print("  - metrics/metrics_auto.json")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()