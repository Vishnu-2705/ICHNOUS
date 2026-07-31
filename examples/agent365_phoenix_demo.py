"""
Agent 365 — OpenTelemetry & Arize Phoenix End-to-End Demo Script.

Demonstrates:
1. Creating OpenTelemetry GenAI spans for a customer support agent.
2. Running Agent 365 Causal Analysis Engine over the span tree.
3. Extracting the root cause span, divergence score, and grounded explanation.
4. Generating an executable Pytest regression artifact.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project directory to sys.path
project_dir = Path(__file__).resolve().parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from agent365.engine.analyzer import analyze_otel_trace
from agent365.engine.regression import generate_pytest_regression_script


def main():
    print("🧠 Agent 365 — OpenTelemetry Causal Engine Demo")
    print("=================================================")

    # 1. Simulate OpenTelemetry GenAI spans emitted by a production agent
    otel_spans = [
        {
            "span_id": "span_agent_plan",
            "trace_id": "trace_support_ticket_882",
            "name": "agent_plan",
            "duration_ms": 120.0,
            "status": {"code": "OK"},
            "attributes": {
                "openinference.span.kind": "AGENT",
                "gen_ai.system": "CustomerSupportBot",
                "input.value": "Customer query: Can I get a full refund for Order #98124 purchased 45 days ago?",
            },
        },
        {
            "span_id": "span_kb_search",
            "parent_span_id": "span_agent_plan",
            "trace_id": "trace_support_ticket_882",
            "name": "search_knowledge_base",
            "duration_ms": 340.0,
            "status": {"code": "OK"},
            "attributes": {
                "openinference.span.kind": "TOOL",
                "tool.name": "search_knowledge_base",
                "retrieval.relevance_score": 0.38,  # Low relevance anomaly
                "document_id": "refund-policy-2023.pdf",
                "note": "Stale 2023 refund policy document returned instead of 2025 policy",
            },
        },
        {
            "span_id": "span_llm_reasoning",
            "parent_span_id": "span_kb_search",
            "trace_id": "trace_support_ticket_882",
            "name": "llm_reasoning_step",
            "duration_ms": 890.0,
            "status": {"code": "OK"},
            "attributes": {
                "openinference.span.kind": "LLM",
                "gen_ai.request.model": "claude-3-5-sonnet-20241022",
                "input.value": "Policy says 30 day return window. Purchase was 45 days ago. Deny refund.",
            },
        },
        {
            "span_id": "span_final_answer",
            "parent_span_id": "span_llm_reasoning",
            "trace_id": "trace_support_ticket_882",
            "name": "final_answer",
            "duration_ms": 40.0,
            "status": {"code": "OK"},
            "attributes": {
                "openinference.span.kind": "CHAIN",
                "output.value": "Your refund request is denied per our 30-day refund policy.",
            },
        },
    ]

    print("\n📥 Ingesting OpenTelemetry GenAI Spans (W3C Trace ID: trace_support_ticket_882)...")
    print(f" -> Total Spans: {len(otel_spans)}")

    # 2. Run Agent 365 Causal Analysis Engine
    print("\n🔍 Running Causal Diagnosis Engine (Divergence Scoring & Backward Walk)...")
    diagnosis_response = analyze_otel_trace(otel_spans)
    diag = diagnosis_response.diagnosis

    print("\n✅ Causal Diagnosis Complete!")
    print("-------------------------------------------------")
    print(f"🎯 Failure Category    : {diag.failure_category}")
    print(f"📍 Root Cause Span ID  : {diag.root_cause_node_id}")
    print(f"📊 Confidence Score    : {diag.confidence:.0%}")
    print(f"🛡️  Evidence Nodes     : {', '.join(diag.evidence_node_ids)}")
    print(f"💬 Explanation         : {diag.explanation}")

    print("\n🛠️  Suggested Code / Prompt Patch:")
    print(f"Target: {diag.suggested_fix.target}")
    print("```diff")
    print(diag.suggested_fix.diff)
    print("```")

    # 3. Export Pytest Regression Test Artifact
    output_test_file = Path("test_agent365_generated_regression.py")
    script = generate_pytest_regression_script(diagnosis_response, otel_spans)
    output_test_file.write_text(script, encoding="utf-8")
    print(f"\n📦 Generated executable Pytest regression artifact: '{output_test_file}'")

    print("\n🎉 Demo completed successfully!")


if __name__ == "__main__":
    main()
