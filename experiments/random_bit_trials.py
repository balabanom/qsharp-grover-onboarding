"""Run the FND-RBIT-001 local-simulator experiment."""

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


EXPERIMENT_ID = "FND-RBIT-001"
QSHARP_CALLABLE = "RandomBit.Main()"
BACKEND = "QDK local simulator (qsharp.run default)"
EXPECTED_RATE = 0.5
ACCEPTANCE_LOWER = 0.45
ACCEPTANCE_UPPER = 0.55
FINAL_TRIAL_COUNT = 1000
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def positive_integer(value: str) -> int:
    """Parse a strictly positive integer for argparse."""
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run repeated RandomBit.Main() shots and generate raw JSON, "
            "a processed summary, and an SVG figure."
        )
    )
    parser.add_argument(
        "--trials",
        required=True,
        type=positive_integer,
        help="number of local-simulator shots",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT,
        help="root beneath which results/ is written (default: repository root)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow a dirty Git tree only when output is outside the repository",
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
    trials: int,
    output_root: Path,
    allow_dirty: bool,
    git_dirty: bool,
) -> bool:
    """Validate safety rules and return whether this is the final run mode."""
    repository_output = is_within(output_root, PROJECT_ROOT)

    if repository_output and trials != FINAL_TRIAL_COUNT:
        parser.error(
            "repository output is reserved for the final 1000-trial run; "
            "use --output-root outside the repository for smoke runs"
        )
    if repository_output and allow_dirty:
        parser.error("--allow-dirty cannot be used with repository output")
    if git_dirty and not allow_dirty:
        parser.error(
            "the Git working tree is dirty; the final run requires a clean tree, "
            "or use --allow-dirty with an external --output-root for a smoke run"
        )

    return repository_output and trials == FINAL_TRIAL_COUNT


def write_json_exclusive(path: Path, value: dict[str, Any]) -> None:
    """Create a JSON file without allowing an existing result to be replaced."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output_file:
        json.dump(value, output_file, indent=2, sort_keys=True)
        output_file.write("\n")


def build_summary(raw: dict[str, Any], source_raw_file: str) -> dict[str, Any]:
    trial_count = raw["trial_count"]
    zero_count = raw["counts"]["Zero"]
    one_count = raw["counts"]["One"]
    zero_rate = zero_count / trial_count
    one_rate = one_count / trial_count
    passed = (
        ACCEPTANCE_LOWER <= zero_rate <= ACCEPTANCE_UPPER
        and ACCEPTANCE_LOWER <= one_rate <= ACCEPTANCE_UPPER
    )

    return {
        "experiment_id": raw["experiment_id"],
        "run_id": raw["run_id"],
        "source_raw_file": source_raw_file,
        "trial_count": trial_count,
        "zero_count": zero_count,
        "one_count": one_count,
        "zero_rate": zero_rate,
        "one_rate": one_rate,
        "expected_rate": EXPECTED_RATE,
        "acceptance_lower": ACCEPTANCE_LOWER,
        "acceptance_upper": ACCEPTANCE_UPPER,
        "absolute_deviation_zero": abs(zero_rate - EXPECTED_RATE),
        "absolute_deviation_one": abs(one_rate - EXPECTED_RATE),
        "pass": passed,
    }


def build_svg(summary: dict[str, Any]) -> str:
    """Build a dependency-free SVG bar chart from a processed result."""
    width = 720
    height = 480
    plot_top = 105
    plot_bottom = 385
    plot_height = plot_bottom - plot_top
    expected_y = plot_bottom - EXPECTED_RATE * plot_height
    bar_width = 150
    bar_positions = (("Zero", 180), ("One", 410))

    bars: list[str] = []
    for label, x_position in bar_positions:
        rate = summary[f"{label.lower()}_rate"]
        count = summary[f"{label.lower()}_count"]
        bar_height = rate * plot_height
        y_position = plot_bottom - bar_height
        bars.extend(
            [
                (
                    f'<rect x="{x_position}" y="{y_position:.2f}" '
                    f'width="{bar_width}" height="{bar_height:.2f}" '
                    'fill="#2563eb" />'
                ),
                (
                    f'<text x="{x_position + bar_width / 2:.0f}" '
                    f'y="{y_position - 10:.2f}" text-anchor="middle" '
                    f'class="value">{count} ({rate:.1%})</text>'
                ),
                (
                    f'<text x="{x_position + bar_width / 2:.0f}" y="415" '
                    f'text-anchor="middle" class="label">{label}</text>'
                ),
            ]
        )

    run_id = escape(str(summary["run_id"]))
    trial_count = summary["trial_count"]
    passed = "PASS" if summary["pass"] else "FAIL"
    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            "  <style>",
            "    text { font-family: Arial, sans-serif; fill: #172033; }",
            "    .title { font-size: 22px; font-weight: 700; }",
            "    .subtitle { font-size: 14px; }",
            "    .value { font-size: 15px; font-weight: 700; }",
            "    .label { font-size: 17px; }",
            "    .axis { stroke: #64748b; stroke-width: 1; }",
            "    .expected { stroke: #dc2626; stroke-width: 2; stroke-dasharray: 7 5; }",
            "  </style>",
            '  <rect width="720" height="480" fill="#ffffff" />',
            (
                f'  <text x="360" y="34" text-anchor="middle" class="title">'
                f'{EXPERIMENT_ID} Random-Bit Distribution</text>'
            ),
            (
                f'  <text x="360" y="58" text-anchor="middle" class="subtitle">'
                f'Run {run_id} · n={trial_count} · frozen-rule result: {passed}</text>'
            ),
            f'  <line x1="110" y1="{plot_bottom}" x2="650" y2="{plot_bottom}" class="axis" />',
            f'  <line x1="110" y1="{plot_top}" x2="110" y2="{plot_bottom}" class="axis" />',
            (
                f'  <line x1="110" y1="{expected_y:.2f}" x2="650" '
                f'y2="{expected_y:.2f}" class="expected" />'
            ),
            (
                f'  <text x="642" y="{expected_y - 8:.2f}" text-anchor="end" '
                'class="subtitle">Expected 50%</text>'
            ),
            '  <text x="98" y="390" text-anchor="end" class="subtitle">0%</text>',
            '  <text x="98" y="250" text-anchor="end" class="subtitle">50%</text>',
            '  <text x="98" y="110" text-anchor="end" class="subtitle">100%</text>',
            *(f"  {bar}" for bar in bars),
            "</svg>",
            "",
        ]
    )


def write_text_exclusive(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as output_file:
        output_file.write(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    output_root = args.output_root.resolve()
    git_commit = git_text("rev-parse", "HEAD")
    git_dirty = bool(git_text("status", "--porcelain"))
    final_run = validate_run_configuration(
        parser,
        trials=args.trials,
        output_root=output_root,
        allow_dirty=args.allow_dirty,
        git_dirty=git_dirty,
    )

    timestamp = datetime.now(timezone.utc)
    timestamp_utc = timestamp.isoformat(timespec="microseconds").replace("+00:00", "Z")
    run_id = f"{EXPERIMENT_ID}_{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}"

    qsharp.init(project_root=".")
    results = qsharp.run(QSHARP_CALLABLE, shots=args.trials)
    outcomes = [str(result) for result in results]
    if len(outcomes) != args.trials:
        raise RuntimeError(
            f"QDK returned {len(outcomes)} outcomes for {args.trials} requested trials"
        )
    unexpected = sorted(set(outcomes) - {"Zero", "One"})
    if unexpected:
        raise RuntimeError(f"unexpected Q# result values: {unexpected}")

    counts = Counter(outcomes)
    raw = {
        "schema_version": "1.0",
        "experiment_id": EXPERIMENT_ID,
        "run_id": run_id,
        "timestamp_utc": timestamp_utc,
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "python_version": platform.python_version(),
        "qdk_version": version("qdk"),
        "backend": BACKEND,
        "qsharp_callable": QSHARP_CALLABLE,
        "trial_count": args.trials,
        "counts": {"Zero": counts["Zero"], "One": counts["One"]},
        "outcomes": outcomes,
        "expected_rate": EXPECTED_RATE,
        "acceptance_lower": ACCEPTANCE_LOWER,
        "acceptance_upper": ACCEPTANCE_UPPER,
    }

    raw_relative = Path("results/raw/fundamentals") / f"{run_id}.json"
    raw_path = output_root / raw_relative
    processed_path = output_root / "results/processed" / f"{run_id}_summary.json"
    figure_path = output_root / "results/figures" / f"{run_id}.svg"

    write_json_exclusive(raw_path, raw)
    persisted_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    summary = build_summary(persisted_raw, raw_relative.as_posix())
    write_json_exclusive(processed_path, summary)
    write_text_exclusive(figure_path, build_svg(summary))

    print(f"Run: {run_id}")
    print(f"Raw: {raw_path}")
    print(f"Processed: {processed_path}")
    print(f"Figure: {figure_path}")
    print(
        f"Zero: {summary['zero_count']} ({summary['zero_rate']:.3f}); "
        f"One: {summary['one_count']} ({summary['one_rate']:.3f})"
    )
    print(f"Frozen 45%-55% rule: {'PASS' if summary['pass'] else 'FAIL'}")

    if final_run and not summary["pass"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
