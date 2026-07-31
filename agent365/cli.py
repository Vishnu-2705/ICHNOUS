"""
Command Line Interface for Agent 365.

Provides CLI commands for engineers and CI/CD pipelines:
- `agent365 diagnose --otlp-file <path>`
- `agent365 diagnose --phoenix-url <url> --trace-id <id>`
- `agent365 export-regression --otlp-file <path> --output test_regression.py`
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from agent365.adapters.otlp import load_otlp_trace_from_file
from agent365.adapters.phoenix import PhoenixAdapter
from agent365.engine.analyzer import analyze_otel_trace
from agent365.engine.regression import generate_pytest_regression_script


def main(args_list: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent365",
        description="Agent 365 — OpenTelemetry-Native Causal Diagnosis Engine",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Diagnose command
    diag_parser = subparsers.add_parser("diagnose", help="Diagnose an OpenTelemetry trace")
    diag_parser.add_argument("--otlp-file", type=str, help="Path to OTLP JSON trace file")
    diag_parser.add_argument("--phoenix-url", type=str, help="Arize Phoenix server URL", default="http://localhost:6006")
    diag_parser.add_argument("--trace-id", type=str, help="Phoenix trace ID")
    diag_parser.add_argument("--annotate", action="store_true", help="Post root-cause annotation back to Phoenix")

    # Export Regression command
    reg_parser = subparsers.add_parser("export-regression", help="Export Pytest regression test artifact")
    reg_parser.add_argument("--otlp-file", type=str, required=True, help="Path to OTLP JSON trace file")
    reg_parser.add_argument("--output", type=str, default="test_agent_regression.py", help="Output Pytest script path")

    args = parser.parse_args(args_list)

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "diagnose":
            if args.otlp_file:
                spans = load_otlp_trace_from_file(args.otlp_file)
            elif args.trace_id:
                adapter = PhoenixAdapter(phoenix_url=args.phoenix_url)
                spans = adapter.fetch_trace_spans(args.trace_id)
            else:
                print("Error: Specify either --otlp-file or --trace-id", file=sys.stderr)
                return 1

            result = analyze_otel_trace(spans)

            if args.trace_id and args.annotate:
                adapter = PhoenixAdapter(phoenix_url=args.phoenix_url)
                adapter.annotate_root_cause(
                    trace_id=args.trace_id,
                    span_id=result.diagnosis.root_cause_node_id,
                    failure_category=result.diagnosis.failure_category,
                    confidence=result.diagnosis.confidence,
                    explanation=result.diagnosis.explanation,
                )

            print(json.dumps(result.model_dump(), indent=2))
            return 0

        elif args.command == "export-regression":
            spans = load_otlp_trace_from_file(args.otlp_file)
            result = analyze_otel_trace(spans)
            script = generate_pytest_regression_script(result, spans)

            output_path = Path(args.output)
            output_path.write_text(script, encoding="utf-8")
            print(f"✅ Generated Pytest regression artifact at '{output_path}'")
            return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
