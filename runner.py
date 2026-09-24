"""Batch runner for the SV investigation pipeline.

The runner deliberately keeps execution and evaluation separate: only each case's
``input`` document is sent to the agent.  Expected results and provenance in the
case corpus remain unavailable to the model and can be used by later evaluators.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import platform
import re
import subprocess
import sys
import time
import traceback
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv
from pydantic import ValidationError

from . import __version__

# ADK Web loads the package-local .env automatically; the standalone runner must
# do the same before config.py reads model and API settings. Existing process
# environment variables retain priority over values in the file.
load_dotenv(Path(__file__).with_name(".env"), override=False)

from .config import MODEL
from .render_report import render_markdown
from .schemas import SVReport


APP_NAME = "sv_investigator_batch"
USER_ID = "batch-runner"
DEFAULT_MANIFEST = Path(__file__).parent / "tests" / "cases" / "manifest.json"
GENERATED_CASE_FILES = (
    "events.jsonl",
    "state.json",
    "final_response.txt",
    "final_report.json",
    "report.md",
    "metrics.json",
    "error.json",
)


@dataclass(frozen=True)
class Case:
    """The model-visible input plus non-sensitive runner labels."""

    case_id: str
    category: str
    purpose: str
    input_path: Path
    input_data: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return cleaned or "unnamed"


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=_jsonable) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cases(
    manifest_path: Path,
    *,
    case_ids: Iterable[str] = (),
    categories: Iterable[str] = (),
) -> tuple[dict[str, Any], list[Case]]:
    """Load selected cases without loading expected answers or provenance files."""

    manifest_path = manifest_path.resolve()
    manifest = _read_json(manifest_path)
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("manifest must contain a 'cases' array")

    requested_ids = set(case_ids)
    requested_categories = set(categories)
    seen: set[str] = set()
    selected: list[Case] = []
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise ValueError("every manifest case must be an object")
        case_id = str(raw.get("case_id", "")).strip()
        if not case_id:
            raise ValueError("every manifest case requires case_id")
        if case_id in seen:
            raise ValueError(f"duplicate case_id in manifest: {case_id}")
        seen.add(case_id)

        category = str(raw.get("category", "uncategorized"))
        if requested_ids and case_id not in requested_ids:
            continue
        if requested_categories and category not in requested_categories:
            continue

        relative_input = raw.get("input")
        if not isinstance(relative_input, str) or not relative_input:
            raise ValueError(f"case {case_id} requires an input path")
        input_path = (manifest_path.parent / relative_input).resolve()
        input_data = _read_json(input_path)
        if not isinstance(input_data, dict):
            raise ValueError(f"case {case_id} input must be a JSON object")
        selected.append(
            Case(
                case_id=case_id,
                category=category,
                purpose=str(raw.get("purpose", "")),
                input_path=input_path,
                input_data=input_data,
            )
        )

    missing = requested_ids - seen
    if missing:
        raise ValueError(f"unknown case_id(s): {', '.join(sorted(missing))}")
    if not selected:
        raise ValueError("no cases matched the requested filters")
    safe_names = [_safe_name(case.case_id) for case in selected]
    collisions = sorted({name for name in safe_names if safe_names.count(name) > 1})
    if collisions:
        raise ValueError(
            "selected case IDs collide as directory names: " + ", ".join(collisions)
        )
    return manifest, selected


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL)
    return match.group(1) if match else stripped


def parse_final_report(state_value: Any, final_text: str = "") -> dict[str, Any]:
    """Return a canonical report, rejecting prose or structurally invalid JSON."""

    candidate = state_value if state_value not in (None, "") else final_text
    if hasattr(candidate, "model_dump"):
        candidate = candidate.model_dump(mode="json")
    if isinstance(candidate, str):
        candidate = json.loads(_strip_json_fence(candidate))
    if not isinstance(candidate, dict):
        raise ValueError("final report is not a JSON object")
    return SVReport.model_validate(candidate).model_dump(mode="json")


def _event_text(event: Any) -> str:
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or []
    return "".join(part.text for part in parts if getattr(part, "text", None))


def _event_record(event: Any, mode: str) -> dict[str, Any]:
    if mode == "full":
        if hasattr(event, "model_dump"):
            return event.model_dump(mode="json", exclude_none=True)
        return {"value": str(event)}
    text = _event_text(event)
    return {
        "id": getattr(event, "id", None),
        "author": getattr(event, "author", None),
        "timestamp": getattr(event, "timestamp", None),
        "text_length": len(text),
        "error_code": getattr(event, "error_code", None),
        "error_message": getattr(event, "error_message", None),
        "usage_metadata": _jsonable(getattr(event, "usage_metadata", None))
        if getattr(event, "usage_metadata", None) is not None
        else None,
    }


def _token_usage(events: list[Any]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for event in events:
        usage = getattr(event, "usage_metadata", None)
        if usage is None:
            continue
        data = usage.model_dump() if hasattr(usage, "model_dump") else {}
        for key, value in data.items():
            if key.endswith("token_count") and isinstance(value, int):
                totals[key] = totals.get(key, 0) + value
    return totals


def _record_count(value: Any) -> int | None:
    if not isinstance(value, dict):
        return None
    for key in ("records", "matches", "results", "items"):
        if isinstance(value.get(key), list):
            return len(value[key])
    features = value.get("features")
    if isinstance(features, dict):
        return sum(len(items) for items in features.values() if isinstance(items, list))
    for key in ("record_count", "match_count", "result_count", "count"):
        if isinstance(value.get(key), int):
            return value[key]
    return None


def collect_metrics(
    *,
    case: Case,
    status: str,
    elapsed_seconds: float,
    state: dict[str, Any],
    events: list[Any],
    report: dict[str, Any] | None,
    error: dict[str, Any] | None,
) -> dict[str, Any]:
    """Collect operational facts only; this is not a biological-quality score."""

    source_keys = {
        "ensembl_overlap": "region_annotation",
        "ensembl_vep": "vep_evidence",
        "gnomad_sv": "database_evidence",
        "clingen_dosage": "clingen_dosage_evidence",
        "clinvar": "clinvar_evidence",
        "dbvar": "dbvar_evidence",
        "dgv": "dgv_evidence",
    }
    baseline = state.get("baseline_evidence")
    if not isinstance(baseline, dict):
        baseline = {}
    sources: dict[str, Any] = {}
    for source, key in source_keys.items():
        # Current sessions store source results under baseline_evidence. The fallback
        # also understands early development states that used top-level source keys.
        value = baseline.get(key, state.get(key))
        sources[source] = {
            "status": value.get("status") if isinstance(value, dict) else None,
            "record_count": _record_count(value),
            "state_key_present": key in baseline or key in state,
        }

    adaptive = state.get("adaptive_tool_results")
    literature = state.get("literature_tool_results")
    state_json = json.dumps(state, ensure_ascii=False, default=_jsonable)
    return {
        "case_id": case.case_id,
        "category": case.category,
        "run_status": status,
        "report_status": report.get("report_status") if report else None,
        "schema_valid": report is not None,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "event_count": len(events),
        "state_character_count": len(state_json),
        "state_keys": sorted(state),
        "token_usage": _token_usage(events),
        "sources": sources,
        "adaptive_result_count": len(adaptive) if isinstance(adaptive, list) else 0,
        "literature_query_count": len(literature) if isinstance(literature, list) else 0,
        "error_type": error.get("type") if error else None,
        "completed_at": _utc_now(),
    }


def _case_is_complete(case_dir: Path) -> bool:
    metrics_path = case_dir / "metrics.json"
    if not metrics_path.exists():
        return False
    try:
        return _read_json(metrics_path).get("run_status") == "complete"
    except (OSError, ValueError, TypeError):
        return False


def _clean_generated_case_files(case_dir: Path) -> None:
    # Only runner-owned files are replaced; user data and unknown files are preserved.
    for name in GENERATED_CASE_FILES:
        (case_dir / name).unlink(missing_ok=True)


async def execute_case(
    case: Case,
    case_dir: Path,
    *,
    timeout_seconds: float,
    save_events: str,
) -> dict[str, Any]:
    """Run one case in an isolated in-memory ADK session and persist all artifacts."""

    # Delayed imports keep corpus inspection and unit tests independent of ADK startup.
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from .agent import root_agent

    case_dir.mkdir(parents=True, exist_ok=True)
    _clean_generated_case_files(case_dir)
    _write_json(case_dir / "input.json", case.input_data)

    session_service = InMemorySessionService()
    session_id = f"{_safe_name(case.case_id)}-{uuid.uuid4().hex[:10]}"
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )
    events: list[Any] = []
    final_text = ""
    report_text = ""
    started = time.monotonic()
    execution_error: dict[str, Any] | None = None

    events_handle = None
    if save_events != "none":
        events_handle = (case_dir / "events.jsonl").open("w", encoding="utf-8")

    async def consume_events() -> None:
        nonlocal final_text, report_text
        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=json.dumps(case.input_data, ensure_ascii=False))],
        )
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session_id,
            new_message=message,
        ):
            events.append(event)
            text = _event_text(event)
            if text:
                final_text = text
                if getattr(event, "author", "") == "ReportAssemblyAgent":
                    report_text = text
            if events_handle is not None:
                record = _event_record(event, save_events)
                events_handle.write(json.dumps(record, ensure_ascii=False, default=_jsonable) + "\n")
                events_handle.flush()

    try:
        await asyncio.wait_for(consume_events(), timeout=timeout_seconds)
    except TimeoutError:
        execution_error = {
            "type": "timeout",
            "message": f"case exceeded {timeout_seconds:g} seconds",
            "traceback": traceback.format_exc(),
        }
    except Exception as exc:  # Preserve the failed case and continue with the batch.
        execution_error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        if events_handle is not None:
            events_handle.close()

    state: dict[str, Any] = {}
    try:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )
        if session is not None:
            state = dict(session.state)
    except Exception as exc:
        if execution_error is None:
            execution_error = {
                "type": "state_retrieval_error",
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
    finally:
        try:
            await runner.close()
        except Exception as exc:
            if execution_error is None:
                execution_error = {
                    "type": "runner_close_error",
                    "message": str(exc),
                    "traceback": traceback.format_exc(),
                }

    elapsed = time.monotonic() - started
    _write_json(case_dir / "state.json", state)
    response_text = report_text or final_text
    (case_dir / "final_response.txt").write_text(response_text, encoding="utf-8")

    report: dict[str, Any] | None = None
    status = "complete"
    if execution_error is not None:
        status = "timeout" if execution_error["type"] == "timeout" else "agent_error"
    else:
        try:
            report = parse_final_report(state.get("final_report"), response_text)
            _write_json(case_dir / "final_report.json", report)
            (case_dir / "report.md").write_text(
                render_markdown(report), encoding="utf-8"
            )
        except (ValueError, TypeError, json.JSONDecodeError, ValidationError) as exc:
            status = "invalid_report"
            execution_error = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }

    if execution_error is not None:
        _write_json(case_dir / "error.json", execution_error)
    metrics = collect_metrics(
        case=case,
        status=status,
        elapsed_seconds=elapsed,
        state=state,
        events=events,
        report=report,
        error=execution_error,
    )
    _write_json(case_dir / "metrics.json", metrics)
    return metrics


def _git_metadata(repo_dir: Path) -> dict[str, Any]:
    def run(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=repo_dir,
                text=True,
                capture_output=True,
                check=True,
                timeout=10,
            )
            return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None

    status = run("status", "--porcelain")
    return {
        "commit": run("rev-parse", "HEAD"),
        "branch": run("branch", "--show-current"),
        "dirty": bool(status) if status is not None else None,
    }


def _runtime_metadata() -> dict[str, Any]:
    try:
        adk_version = version("google-adk")
    except PackageNotFoundError:
        adk_version = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "google_adk": adk_version,
    }


def _new_run_dir(output_root: Path) -> Path:
    base = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_safe_name(MODEL)}"
    candidate = output_root / base
    suffix = 2
    while candidate.exists():
        candidate = output_root / f"{base}_{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


def _write_summary(run_dir: Path, metrics: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for item in metrics:
        status = str(item.get("run_status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    summary = {
        "generated_at": _utc_now(),
        "total": len(metrics),
        "status_counts": counts,
        "all_complete": bool(metrics) and counts.get("complete", 0) == len(metrics),
        "cases": metrics,
    }
    _write_json(run_dir / "summary.json", summary)

    columns = (
        "case_id",
        "category",
        "run_status",
        "report_status",
        "schema_valid",
        "elapsed_seconds",
        "event_count",
        "state_character_count",
        "adaptive_result_count",
        "literature_query_count",
        "error_type",
    )
    with (run_dir / "summary.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for item in metrics:
            writer.writerow({key: item.get(key) for key in columns})
    return summary


async def run_batch(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    manifest_path = Path(args.manifest).resolve()
    manifest, cases = load_cases(
        manifest_path,
        case_ids=args.case,
        categories=args.category,
    )
    if args.list:
        for case in cases:
            print(f"{case.case_id}\t{case.category}\t{case.purpose}")
        return manifest_path.parent, {"listed": len(cases), "all_complete": True}

    if args.run_dir:
        run_dir = Path(args.run_dir).resolve()
        if run_dir.exists() and not (args.resume or args.rerun_completed):
            raise ValueError("existing --run-dir requires --resume or --rerun-completed")
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        if args.resume or args.rerun_completed:
            raise ValueError("--resume and --rerun-completed require --run-dir")
        run_dir = _new_run_dir(Path(args.output).resolve())

    run_manifest_path = run_dir / "run_manifest.json"
    selected_metadata = [
        {
            "case_id": case.case_id,
            "category": case.category,
            "purpose": case.purpose,
            "input": str(case.input_path),
        }
        for case in cases
    ]
    if run_manifest_path.exists():
        run_manifest = _read_json(run_manifest_path)
        previous_manifest = run_manifest.get("source_manifest")
        if previous_manifest and Path(previous_manifest).resolve() != manifest_path:
            raise ValueError("run directory belongs to a different source manifest")
        previous_model = run_manifest.get("model")
        if previous_model and previous_model != MODEL:
            raise ValueError(
                f"run directory used model {previous_model!r}, not current {MODEL!r}"
            )
        previous_ids = [
            item.get("case_id") for item in run_manifest.get("selected_cases", [])
        ]
        current_ids = [case.case_id for case in cases]
        if previous_ids and previous_ids != current_ids:
            raise ValueError("run directory was created with a different case selection")
        run_manifest.setdefault("resume_history", []).append(_utc_now())
    else:
        run_manifest = {
            "project_version": __version__,
            "runner_version": "1.0.1",
            "started_at": _utc_now(),
            "source_manifest": str(manifest_path),
            "corpus_version": manifest.get("corpus_version"),
            "model": MODEL,
            "runtime": _runtime_metadata(),
            "git": _git_metadata(Path(__file__).parent),
        }
    run_manifest.update(
        {
            "selected_cases": selected_metadata,
            "config": {
                "case_timeout_seconds": args.case_timeout,
                "save_events": args.save_events,
                "fail_fast": args.fail_fast,
            },
        }
    )
    _write_json(run_manifest_path, run_manifest)

    stopped_early = False
    for index, case in enumerate(cases, start=1):
        case_dir = run_dir / "cases" / _safe_name(case.case_id)
        if args.resume and not args.rerun_completed and _case_is_complete(case_dir):
            print(f"[{index}/{len(cases)}] {case.case_id}: skipped (complete)")
            continue
        print(f"[{index}/{len(cases)}] {case.case_id}: running", flush=True)
        metrics = await execute_case(
            case,
            case_dir,
            timeout_seconds=args.case_timeout,
            save_events=args.save_events,
        )
        print(f"[{index}/{len(cases)}] {case.case_id}: {metrics['run_status']}")
        if args.fail_fast and metrics["run_status"] != "complete":
            stopped_early = True
            break

    all_metrics: list[dict[str, Any]] = []
    for case in cases:
        path = run_dir / "cases" / _safe_name(case.case_id) / "metrics.json"
        if path.exists():
            all_metrics.append(_read_json(path))
    summary = _write_summary(run_dir, all_metrics)
    summary["stopped_early"] = stopped_early
    summary["selected_case_count"] = len(cases)
    summary["all_complete"] = (
        summary["total"] == len(cases)
        and summary["status_counts"].get("complete", 0) == len(cases)
    )
    _write_json(run_dir / "summary.json", summary)
    run_manifest["finished_at"] = _utc_now()
    run_manifest["summary"] = {
        "total_artifacts": summary["total"],
        "selected_case_count": len(cases),
        "status_counts": summary["status_counts"],
        "stopped_early": stopped_early,
    }
    _write_json(run_manifest_path, run_manifest)
    return run_dir, summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the SV investigation agent over a case manifest."
    )
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, type=Path)
    parser.add_argument("--output", default=Path(__file__).parent / "runs", type=Path)
    parser.add_argument("--run-dir", type=Path, help="Existing/new explicit run directory")
    parser.add_argument("--case", action="append", default=[], help="Select case ID")
    parser.add_argument(
        "--category", action="append", default=[], help="Select case category"
    )
    parser.add_argument("--case-timeout", type=float, default=600.0)
    parser.add_argument("--resume", action="store_true", help="Skip completed cases")
    parser.add_argument(
        "--rerun-completed",
        action="store_true",
        help="Run all selected cases again in the specified run directory",
    )
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument(
        "--save-events", choices=("full", "summary", "none"), default="full"
    )
    parser.add_argument("--list", action="store_true", help="List selected cases only")
    return parser


def main(argv: list[str] | None = None) -> int:
    # Windows may expose a legacy console encoding even when paths contain CJK
    # characters. Replacement is preferable to losing an otherwise completed run.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    if args.case_timeout <= 0:
        print("error: --case-timeout must be positive", file=sys.stderr)
        return 2
    try:
        run_dir, summary = asyncio.run(run_batch(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    if args.list:
        return 0
    print(f"Run artifacts: {run_dir}")
    return 0 if summary.get("all_complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())
