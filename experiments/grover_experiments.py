"""Run the frozen Stage 1 Grover simulator experiment suite."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
from typing import Any, Sequence

from qdk import qsharp


SCHEMA_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_IDS = ("GRV-BASE-001", "GRV-TARGET-001", "GRV-ITER-001")
QSHARP_CALLABLE = "Grover.RunGroverSearch(target, iterations)"
BACKEND = "QDK local simulator (qsharp.run default)"
CANDIDATES = (0, 1, 2, 3)
UNIFORM_LOWER = 0.20
UNIFORM_UPPER = 0.30

FINAL_CONFIGURATIONS: dict[str, list[dict[str, int]]] = {
    "GRV-BASE-001": [{"target": 2, "iterations": 1, "shots": 1000}],
    "GRV-TARGET-001": [
        {"target": target, "iterations": 1, "shots": 250}
        for target in CANDIDATES
    ],
    "GRV-ITER-001": [
        {"target": 2, "iterations": iterations, "shots": 1000}
        for iterations in (0, 1, 2)
    ],
}

SMOKE_CONFIGURATIONS: dict[str, list[dict[str, int]]] = {
    "GRV-BASE-001": [{"target": 2, "iterations": 1, "shots": 4}],
    "GRV-TARGET-001": [
        {"target": target, "iterations": 1, "shots": 2}
        for target in CANDIDATES
    ],
    "GRV-ITER-001": [
        {"target": 2, "iterations": iterations, "shots": 8}
        for iterations in (0, 1, 2)
    ],
}

ACCEPTANCE_RULES: dict[str, dict[str, Any]] = {
    "GRV-BASE-001": {
        "type": "exact_target",
        "condition": "all 1000 outcomes equal target 2",
        "accepted_non_target_outcomes": 0,
    },
    "GRV-TARGET-001": {
        "type": "exact_target_per_configuration",
        "condition": "all 250 outcomes equal the configured target for every target 0..3",
        "accepted_non_target_outcomes": 0,
    },
    "GRV-ITER-001": {
        "type": "iteration_specific",
        "iteration_1": "all 1000 outcomes equal target 2",
        "iterations_0_and_2": {
            "condition": "every candidate rate is within the inclusive band",
            "lower_inclusive": UNIFORM_LOWER,
            "upper_inclusive": UNIFORM_UPPER,
        },
    },
}


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the frozen Stage 1 Grover simulator experiment suite."
    )
    parser.add_argument("--mode", required=True, choices=("smoke", "final"))
    parser.add_argument(
        "--output-root",
        type=Path,
        help="root beneath which results/ is written; required for smoke mode",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow a dirty Git tree only for smoke output outside the repository",
    )
    return parser


def git_text(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def validate_run_configuration(
    parser: argparse.ArgumentParser,
    *,
    mode: str,
    output_root_argument: Path | None,
    allow_dirty: bool,
    git_dirty: bool,
) -> Path:
    """Enforce the separation between external smoke output and final evidence."""
    if mode == "final":
        output_root = (
            PROJECT_ROOT
            if output_root_argument is None
            else output_root_argument.resolve()
        )
        if output_root != PROJECT_ROOT:
            parser.error("final mode writes only to the repository result directories")
        if allow_dirty:
            parser.error("--allow-dirty is prohibited in final mode")
        if git_dirty:
            parser.error("final mode requires an initially clean Git working tree")
        return output_root

    if output_root_argument is None:
        parser.error("smoke mode requires --output-root outside the repository")
    output_root = output_root_argument.resolve()
    if is_within(output_root, PROJECT_ROOT):
        parser.error("smoke mode must write outside the repository")
    if git_dirty and not allow_dirty:
        parser.error("the Git tree is dirty; pass --allow-dirty for an external smoke run")
    return output_root


def protect_final_suite() -> None:
    """Refuse a rerun if any final Grover raw result is already present."""
    raw_directory = PROJECT_ROOT / "results/raw/grover"
    existing = sorted(
        path
        for experiment_id in EXPERIMENT_IDS
        for path in raw_directory.glob(f"{experiment_id}_*.json")
    )
    if existing:
        relative = ", ".join(str(path.relative_to(PROJECT_ROOT)) for path in existing)
        raise RuntimeError(
            "final Grover raw results already exist; refusing to create a second "
            f"Stage 1 suite: {relative}"
        )


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output_file:
        json.dump(value, output_file, indent=2, sort_keys=True)
        output_file.write("\n")


def write_text_exclusive(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output_file:
        output_file.write(value)


def theoretical_probabilities(target: int, iterations: int) -> dict[str, float]:
    if iterations == 1:
        return {str(candidate): float(candidate == target) for candidate in CANDIDATES}
    return {str(candidate): 0.25 for candidate in CANDIDATES}


def execute_experiment(
    experiment_id: str,
    configurations: list[dict[str, int]],
    *,
    mode: str,
    suite_id: str,
    timestamp_utc: str,
    git_commit: str,
    git_dirty: bool,
    python_version: str,
    qdk_version: str,
) -> dict[str, Any]:
    outcomes: list[dict[str, int]] = []
    aggregate_counts: Counter[int] = Counter()
    theory: list[dict[str, Any]] = []

    for configuration_index, configuration in enumerate(configurations):
        target = configuration["target"]
        iterations = configuration["iterations"]
        shots = configuration["shots"]
        expression = f"Grover.RunGroverSearch({target}, {iterations})"
        results = qsharp.run(expression, shots=shots)
        if len(results) != shots:
            raise RuntimeError(
                f"{experiment_id} configuration {configuration_index}: QDK returned "
                f"{len(results)} outcomes for {shots} requested shots"
            )

        for configuration_shot_index, result in enumerate(results):
            outcome = int(result)
            if outcome not in CANDIDATES:
                raise RuntimeError(f"unexpected Grover result value: {outcome}")
            outcomes.append(
                {
                    "shot_index": len(outcomes),
                    "configuration_index": configuration_index,
                    "configuration_shot_index": configuration_shot_index,
                    "target": target,
                    "iterations": iterations,
                    "outcome": outcome,
                }
            )
            aggregate_counts[outcome] += 1

        theory.append(
            {
                "target": target,
                "iterations": iterations,
                "probabilities": theoretical_probabilities(target, iterations),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "suite_id": suite_id,
        "experiment_id": experiment_id,
        "mode": mode,
        "timestamp_utc": timestamp_utc,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "python_version": python_version,
        "qdk_version": qdk_version,
        "backend": BACKEND,
        "qsharp_callable": QSHARP_CALLABLE,
        "configuration": configurations,
        "frozen_final_configuration": FINAL_CONFIGURATIONS[experiment_id],
        "theoretical_probabilities": theory,
        "acceptance_rule": ACCEPTANCE_RULES[experiment_id],
        "outcomes": outcomes,
        "counts": {
            str(candidate): aggregate_counts[candidate] for candidate in CANDIDATES
        },
    }


def configuration_passes(
    experiment_id: str,
    *,
    iterations: int,
    target: int,
    counts: dict[str, int],
    shots: int,
) -> bool:
    if experiment_id in ("GRV-BASE-001", "GRV-TARGET-001") or iterations == 1:
        return counts[str(target)] == shots
    return all(
        UNIFORM_LOWER <= counts[str(candidate)] / shots <= UNIFORM_UPPER
        for candidate in CANDIDATES
    )


def build_summary(raw: dict[str, Any], source_raw_file: str) -> dict[str, Any]:
    final_mode = raw["mode"] == "final"
    summaries: list[dict[str, Any]] = []
    measured_rates: dict[str, dict[str, float]] = {}
    absolute_deviations: dict[str, dict[str, float]] = {}

    for configuration_index, configuration in enumerate(raw["configuration"]):
        target = configuration["target"]
        iterations = configuration["iterations"]
        shots = configuration["shots"]
        selected = [
            shot
            for shot in raw["outcomes"]
            if shot["configuration_index"] == configuration_index
        ]
        counter = Counter(shot["outcome"] for shot in selected)
        counts = {str(candidate): counter[candidate] for candidate in CANDIDATES}
        rates = {
            str(candidate): counts[str(candidate)] / shots for candidate in CANDIDATES
        }
        expected = theoretical_probabilities(target, iterations)
        deviations = {
            str(candidate): abs(rates[str(candidate)] - expected[str(candidate)])
            for candidate in CANDIDATES
        }
        key = f"target={target},iterations={iterations}"
        measured_rates[key] = rates
        absolute_deviations[key] = deviations
        passes = configuration_passes(
            raw["experiment_id"],
            iterations=iterations,
            target=target,
            counts=counts,
            shots=shots,
        )
        summaries.append(
            {
                "configuration_index": configuration_index,
                "target": target,
                "iterations": iterations,
                "shots": shots,
                "outcome_counts": counts,
                "outcome_rates": rates,
                "target_success_count": counts[str(target)],
                "target_success_rate": rates[str(target)],
                "theoretical_target_success_rate": expected[str(target)],
                "absolute_deviation_from_theory": deviations[str(target)],
                "pass": passes if final_mode else None,
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "suite_id": raw["suite_id"],
        "experiment_id": raw["experiment_id"],
        "source_raw_file": source_raw_file,
        "configuration_summaries": summaries,
        "theoretical_probabilities": raw["theoretical_probabilities"],
        "measured_rates": measured_rates,
        "absolute_deviations": absolute_deviations,
        "acceptance_rule": raw["acceptance_rule"],
        "pass": all(item["pass"] for item in summaries) if final_mode else None,
    }


def svg_document(title: str, subtitle: str, elements: list[str]) -> str:
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="840" height="520" '
            'viewBox="0 0 840 520">',
            "  <style>",
            "    text { font-family: Arial, sans-serif; fill: #172033; }",
            "    .title { font-size: 22px; font-weight: 700; }",
            "    .subtitle { font-size: 13px; }",
            "    .label { font-size: 15px; }",
            "    .value { font-size: 13px; font-weight: 700; }",
            "    .axis { stroke: #64748b; stroke-width: 1; }",
            "    .theory { stroke: #dc2626; stroke-width: 2; fill: none; }",
            "  </style>",
            '  <rect width="840" height="520" fill="#ffffff" />',
            f'  <text x="420" y="34" text-anchor="middle" class="title">{escape(title)}</text>',
            f'  <text x="420" y="58" text-anchor="middle" class="subtitle">{escape(subtitle)}</text>',
            '  <line x1="90" y1="430" x2="790" y2="430" class="axis" />',
            '  <line x1="90" y1="100" x2="90" y2="430" class="axis" />',
            '  <text x="78" y="435" text-anchor="end" class="subtitle">0%</text>',
            '  <text x="78" y="270" text-anchor="end" class="subtitle">50%</text>',
            '  <text x="78" y="105" text-anchor="end" class="subtitle">100%</text>',
            *elements,
            "</svg>",
            "",
        ]
    )


def build_baseline_svg(summary: dict[str, Any]) -> str:
    item = summary["configuration_summaries"][0]
    elements: list[str] = []
    for candidate in CANDIDATES:
        x = 145 + candidate * 160
        rate = item["outcome_rates"][str(candidate)]
        count = item["outcome_counts"][str(candidate)]
        height = rate * 330
        y = 430 - height
        color = "#16a34a" if candidate == 2 else "#2563eb"
        elements.extend(
            [
                f'  <rect x="{x}" y="{y:.2f}" width="90" height="{height:.2f}" fill="{color}" />',
                f'  <text x="{x + 45}" y="{max(y - 9, 88):.2f}" text-anchor="middle" class="value">{count} ({rate:.1%})</text>',
                f'  <text x="{x + 45}" y="458" text-anchor="middle" class="label">{candidate}{" (target)" if candidate == 2 else ""}</text>',
            ]
        )
        expected = 1.0 if candidate == 2 else 0.0
        marker_y = 430 - expected * 330
        elements.append(
            f'  <line x1="{x - 5}" y1="{marker_y:.2f}" x2="{x + 95}" y2="{marker_y:.2f}" class="theory" />'
        )
    return svg_document(
        "GRV-BASE-001 Outcome Distribution",
        f"Suite {summary['suite_id']} · target 2 · red markers show theory",
        elements,
    )


def build_target_svg(summary: dict[str, Any]) -> str:
    elements = ['  <line x1="100" y1="100" x2="780" y2="100" class="theory" />']
    for item in summary["configuration_summaries"]:
        target = item["target"]
        x = 145 + target * 160
        rate = item["target_success_rate"]
        height = rate * 330
        y = 430 - height
        elements.extend(
            [
                f'  <rect x="{x}" y="{y:.2f}" width="90" height="{height:.2f}" fill="#2563eb" />',
                f'  <text x="{x + 45}" y="{max(y - 9, 88):.2f}" text-anchor="middle" class="value">{rate:.1%}</text>',
                f'  <text x="{x + 45}" y="458" text-anchor="middle" class="label">Target {target}</text>',
            ]
        )
    return svg_document(
        "GRV-TARGET-001 Target Success",
        f"Suite {summary['suite_id']} · red line is theoretical 100%",
        elements,
    )


def build_iteration_svg(summary: dict[str, Any]) -> str:
    positions = (190, 420, 650)
    elements: list[str] = []
    theory_points: list[str] = []
    for x, item in zip(positions, summary["configuration_summaries"], strict=True):
        rate = item["target_success_rate"]
        expected = item["theoretical_target_success_rate"]
        height = rate * 330
        y = 430 - height
        expected_y = 430 - expected * 330
        theory_points.append(f"{x + 45},{expected_y:.2f}")
        elements.extend(
            [
                f'  <rect x="{x}" y="{y:.2f}" width="90" height="{height:.2f}" fill="#2563eb" />',
                f'  <text x="{x + 45}" y="{max(y - 9, 88):.2f}" text-anchor="middle" class="value">{rate:.1%}</text>',
                f'  <text x="{x + 45}" y="458" text-anchor="middle" class="label">Iterations {item["iterations"]}</text>',
            ]
        )
    elements.append(
        f'  <polyline points="{" ".join(theory_points)}" class="theory" />'
    )
    for point in theory_points:
        x, y = point.split(",")
        elements.append(f'  <circle cx="{x}" cy="{y}" r="5" fill="#dc2626" />')
    return svg_document(
        "GRV-ITER-001 Target Success by Iteration",
        f"Suite {summary['suite_id']} · target 2 · red points show theory",
        elements,
    )


def build_svg(summary: dict[str, Any]) -> str:
    builders = {
        "GRV-BASE-001": build_baseline_svg,
        "GRV-TARGET-001": build_target_svg,
        "GRV-ITER-001": build_iteration_svg,
    }
    return builders[summary["experiment_id"]](summary)


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    # This is the single initial tree-state check for the complete invocation.
    git_commit = git_text("rev-parse", "HEAD")
    git_dirty = bool(git_text("status", "--porcelain"))
    output_root = validate_run_configuration(
        parser,
        mode=args.mode,
        output_root_argument=args.output_root,
        allow_dirty=args.allow_dirty,
        git_dirty=git_dirty,
    )
    if args.mode == "final":
        protect_final_suite()

    timestamp = datetime.now(timezone.utc)
    timestamp_utc = timestamp.isoformat(timespec="microseconds").replace("+00:00", "Z")
    suite_id = timestamp.strftime("%Y%m%dT%H%M%S%fZ")
    configurations = (
        FINAL_CONFIGURATIONS if args.mode == "final" else SMOKE_CONFIGURATIONS
    )
    python_version = platform.python_version()
    qdk_version = version("qdk")

    qsharp.init(project_root=".")
    summaries: list[dict[str, Any]] = []
    for experiment_id in EXPERIMENT_IDS:
        raw = execute_experiment(
            experiment_id,
            configurations[experiment_id],
            mode=args.mode,
            suite_id=suite_id,
            timestamp_utc=timestamp_utc,
            git_commit=git_commit,
            git_dirty=git_dirty,
            python_version=python_version,
            qdk_version=qdk_version,
        )
        filename = f"{experiment_id}_{suite_id}"
        raw_relative = Path("results/raw/grover") / f"{filename}.json"
        processed_relative = Path("results/processed/grover") / f"{filename}.json"
        figure_relative = Path("results/figures/grover") / f"{filename}.svg"
        raw_path = output_root / raw_relative
        processed_path = output_root / processed_relative
        figure_path = output_root / figure_relative

        write_json_exclusive(raw_path, raw)
        persisted_raw = json.loads(raw_path.read_text(encoding="utf-8"))
        summary = build_summary(persisted_raw, raw_relative.as_posix())
        write_json_exclusive(processed_path, summary)
        write_text_exclusive(figure_path, build_svg(summary))
        summaries.append(summary)

        print(f"{experiment_id} raw: {raw_path}")
        print(f"{experiment_id} processed: {processed_path}")
        print(f"{experiment_id} figure: {figure_path}")

    print(f"Suite ID: {suite_id}")
    if args.mode == "smoke":
        print("Suite result: SMOKE COMPLETE (acceptance not evaluated)")
        return 0

    suite_passed = all(summary["pass"] for summary in summaries)
    print(f"Suite result: {'PASS' if suite_passed else 'FAIL'}")
    return 0 if suite_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
