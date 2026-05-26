#!/usr/bin/env python3
"""Aggregate FSI evaluation results into benchmark.json and benchmark.md.

Extends the skill-creator benchmark aggregation with FSI-specific metrics:
financial accuracy scores, data provenance rates, and regulatory compliance.

Usage:
  aggregate_fsi_benchmark.py <evals_dir>
"""
import json
import sys
from pathlib import Path


def load_gradings(evals_dir: Path) -> list[dict]:
    runs_dir = evals_dir / "runs"
    if not runs_dir.exists():
        return []
    gradings = []
    for run_dir in sorted(runs_dir.iterdir()):
        grading_file = run_dir / "grading.json"
        if grading_file.exists():
            gradings.append(json.loads(grading_file.read_text()))
    return gradings


def compute_pass_rate(gradings: list[dict]) -> float:
    total, passed = 0, 0
    for g in gradings:
        summary = g.get("summary", {})
        total += summary.get("total", 0)
        passed += summary.get("passed", 0)
    return passed / total if total > 0 else 0.0


def compute_fsi_accuracy(gradings: list[dict]) -> dict:
    """Extract FSI-specific accuracy metrics from grading results."""
    checks = {
        "arithmetic_integrity": {"passed": 0, "total": 0},
        "reasonableness": {"passed": 0, "total": 0},
        "data_provenance": {"passed": 0, "total": 0},
        "regulatory_compliance": {"passed": 0, "total": 0},
        "format_compliance": {"passed": 0, "total": 0},
    }
    for g in gradings:
        fsi = g.get("fsi_checks", {})
        for check_name, check_data in fsi.items():
            if check_name in checks:
                checks[check_name]["total"] += 1
                if check_data.get("passed"):
                    checks[check_name]["passed"] += 1

    result = {}
    for name, counts in checks.items():
        rate = counts["passed"] / counts["total"] if counts["total"] > 0 else None
        result[name] = {
            "pass_rate": rate,
            "passed": counts["passed"],
            "total": counts["total"],
        }
    return result


def compute_timing(gradings: list[dict]) -> dict:
    durations = []
    for g in gradings:
        timing = g.get("timing", {})
        d = timing.get("executor_duration_seconds")
        if d is not None:
            durations.append(d)
    if not durations:
        return {"mean_seconds": None, "min_seconds": None, "max_seconds": None}
    return {
        "mean_seconds": sum(durations) / len(durations),
        "min_seconds": min(durations),
        "max_seconds": max(durations),
    }


def generate_benchmark(evals_dir: str):
    evals_path = Path(evals_dir)
    gradings = load_gradings(evals_path)

    if not gradings:
        print(f"No grading results found in {evals_path}/runs/")
        sys.exit(1)

    pass_rate = compute_pass_rate(gradings)
    fsi_accuracy = compute_fsi_accuracy(gradings)
    timing = compute_timing(gradings)

    benchmark = {
        "runs": len(gradings),
        "overall_pass_rate": round(pass_rate, 4),
        "fsi_accuracy": fsi_accuracy,
        "timing": timing,
        "quality_gate": {
            "overall_pass_rate_met": pass_rate >= 0.80,
            "financial_accuracy_met": all(
                v["pass_rate"] is None or v["pass_rate"] >= 0.90
                for v in fsi_accuracy.values()
            ),
        },
    }

    benchmark_file = evals_path / "benchmark.json"
    benchmark_file.write_text(json.dumps(benchmark, indent=2) + "\n")
    print(f"Wrote {benchmark_file}")

    # Generate markdown summary
    md_lines = [
        "# FSI Benchmark Report",
        "",
        f"**Runs:** {len(gradings)}",
        f"**Overall Pass Rate:** {pass_rate:.1%}",
        "",
        "## Financial Accuracy",
        "",
        "| Check | Pass Rate | Passed | Total |",
        "|-------|-----------|--------|-------|",
    ]
    for name, data in fsi_accuracy.items():
        rate_str = f"{data['pass_rate']:.1%}" if data["pass_rate"] is not None else "N/A"
        md_lines.append(f"| {name} | {rate_str} | {data['passed']} | {data['total']} |")

    md_lines.extend([
        "",
        "## Timing",
        "",
        f"- Mean: {timing['mean_seconds']:.1f}s" if timing["mean_seconds"] else "- No timing data",
        "",
        "## Quality Gate",
        "",
        f"- Overall pass rate >= 80%: {'PASS' if benchmark['quality_gate']['overall_pass_rate_met'] else 'FAIL'}",
        f"- Financial accuracy >= 90%: {'PASS' if benchmark['quality_gate']['financial_accuracy_met'] else 'FAIL'}",
    ])

    md_file = evals_path / "benchmark.md"
    md_file.write_text("\n".join(md_lines) + "\n")
    print(f"Wrote {md_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: aggregate_fsi_benchmark.py <evals_dir>")
        sys.exit(1)
    generate_benchmark(sys.argv[1])


if __name__ == "__main__":
    main()
