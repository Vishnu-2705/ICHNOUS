"""
Regression test artifact generator module for TraceMind.

Generates RegressionTest Pydantic model artifacts and JSON representations from Trace and DiagnosisResult.
Does NOT execute tests.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import networkx as nx

try:
    from models.trace import DiagnosisResult, RegressionAssertion, RegressionTest, Trace
except ImportError:
    from backend.models.trace import DiagnosisResult, RegressionAssertion, RegressionTest, Trace


def generate_regression_test(
    trace: Trace,
    diagnosis: DiagnosisResult,
    g: Optional[nx.DiGraph] = None,
) -> RegressionTest:
    """
    Generate a RegressionTest artifact from a Trace and DiagnosisResult.

    Extracts:
    - minimal inputs (initial task from first plan node)
    - recorded tool outputs and observations for evidence nodes
    - regression assertion (failure category & root cause pattern)
    """
    # 1. Extract initial task from plan node
    initial_task = ""
    for node in trace.nodes:
        ntype = node.type.value if hasattr(node.type, "value") else str(node.type)
        if ntype == "plan":
            initial_task = node.content
            break
    if not initial_task and trace.nodes:
        initial_task = trace.nodes[0].content

    # 2. Collect recorded tool outputs / observations for evidence nodes
    evidence_set = set(diagnosis.evidence_node_ids)
    recorded_outputs: List[Dict[str, Any]] = []

    for node in trace.nodes:
        ntype = node.type.value if hasattr(node.type, "value") else str(node.type)
        if node.id in evidence_set and ntype in ("tool_call", "observation", "delegation"):
            recorded_outputs.append({
                "node_id": node.id,
                "type": ntype,
                "content": node.content,
                "metadata": node.metadata,
            })

    # Fallback if no specific tool outputs matched
    if not recorded_outputs:
        for node in trace.nodes:
            if node.id in evidence_set:
                ntype = node.type.value if hasattr(node.type, "value") else str(node.type)
                recorded_outputs.append({
                    "node_id": node.id,
                    "type": ntype,
                    "content": node.content,
                    "metadata": node.metadata,
                })

    # 3. Construct root cause pattern
    root_content = ""
    if g and g.has_node(diagnosis.root_cause_node_id):
        root_content = g.nodes[diagnosis.root_cause_node_id].get("content", "")[:100]
    else:
        for node in trace.nodes:
            if node.id == diagnosis.root_cause_node_id:
                root_content = node.content[:100]
                break

    root_cause_pattern = f"Root cause at node '{diagnosis.root_cause_node_id}': {root_content}"

    # 4. Build RegressionTest object
    assertion = RegressionAssertion(
        failure_category=diagnosis.failure_category,
        root_cause_pattern=root_cause_pattern,
    )

    minimal_inputs = {
        "initial_task": initial_task,
        "trace_id": trace.id,
        "description": trace.description,
    }

    return RegressionTest(
        trace_id=trace.id,
        trace_name=trace.name,
        failure_category=diagnosis.failure_category,
        root_cause_node_id=diagnosis.root_cause_node_id,
        minimal_inputs=minimal_inputs,
        recorded_tool_outputs=recorded_outputs,
        assertion=assertion,
    )


def generate_regression_test_dict(
    trace: Trace,
    diagnosis: DiagnosisResult,
    g: Optional[nx.DiGraph] = None,
) -> Dict[str, Any]:
    """Return regression test artifact as a dict."""
    test_obj = generate_regression_test(trace, diagnosis, g)
    return test_obj.model_dump()


def generate_regression_test_json(
    trace: Trace,
    diagnosis: DiagnosisResult,
    g: Optional[nx.DiGraph] = None,
) -> str:
    """Return regression test artifact as a formatted JSON string."""
    test_obj = generate_regression_test(trace, diagnosis, g)
    return json.dumps(test_obj.model_dump(), indent=2)
