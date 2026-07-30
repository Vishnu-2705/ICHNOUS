"""
LLM Diagnosis Integration for TraceMind.

Makes structured LLM calls to generate a DiagnosisResult for a given RootCauseCandidate,
evidence nodes, and failure taxonomy. Features schema validation, retries on malformed JSON,
and groundedness validation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, List, Optional
import networkx as nx

try:
    from diagnosis.taxonomy import TAXONOMY_LIST
    from diagnosis.validator import validate_groundedness
    from models.trace import DiagnosisResult, RootCauseCandidate, SuggestedFix
except ImportError:
    from backend.diagnosis.taxonomy import TAXONOMY_LIST
    from backend.diagnosis.validator import validate_groundedness
    from backend.models.trace import DiagnosisResult, RootCauseCandidate, SuggestedFix

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are TraceMind, an expert AI-agent debugger.
Your task is to analyze a root cause candidate and evidence nodes from an execution failure,
classify the failure into EXACTLY ONE category from the provided failure taxonomy, explain the causal chain, and suggest a concrete fix.

You MUST respond with valid JSON matching this exact schema — no markdown formatting, no conversational text, ONLY the raw JSON object:

{
  "failure_category": "<one of the taxonomy values>",
  "confidence": <float between 0.0 and 1.0>,
  "root_cause_node_id": "<node ID string>",
  "evidence_node_ids": ["<node_id>", ...],
  "explanation": "<2-4 sentences explaining the causal chain in plain language>",
  "suggested_fix": {
    "type": "<one of: prompt_patch | tool_schema_fix | retry_policy | guardrail_addition>",
    "target": "<target component or file to change>",
    "diff": "<concrete fix instructions or patch diff>"
  },
  "grounded": true
}

RULES:
1. failure_category MUST be one of: %(taxonomy)s
2. root_cause_node_id MUST match the provided root cause candidate node ID.
3. evidence_node_ids MUST be a list of node IDs from the provided evidence nodes.
4. Return ONLY valid JSON.
"""

USER_PROMPT_TEMPLATE = """## Root Cause Candidate
Node ID: {node_id}
Divergence Score: {divergence_score:.2f}
Critical Path: {critical_path}

## Evidence Nodes ({node_count} nodes)
{evidence_nodes_json}

## Allowed Failure Taxonomy
{taxonomy_str}

Analyze the evidence and provide your diagnosis as strict JSON.
"""


def _build_prompts(
    candidate: RootCauseCandidate,
    evidence_nodes: List[Dict[str, Any]],
    taxonomy: List[str],
) -> tuple[str, str]:
    taxonomy_str = ", ".join(taxonomy)
    system = SYSTEM_PROMPT % {"taxonomy": taxonomy_str}

    nodes_json = json.dumps(evidence_nodes, indent=2)
    critical_path_str = " -> ".join(candidate.critical_path) if candidate.critical_path else candidate.node_id

    user = USER_PROMPT_TEMPLATE.format(
        node_id=candidate.node_id,
        divergence_score=candidate.divergence_score,
        critical_path=critical_path_str,
        node_count=len(evidence_nodes),
        evidence_nodes_json=nodes_json,
        taxonomy_str=taxonomy_str,
    )
    return system, user


def _clean_json_response(raw_response: str) -> str:
    """Strip markdown backticks or surrounding whitespace from LLM response."""
    text = raw_response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def diagnose_with_llm(
    candidate: RootCauseCandidate,
    evidence_nodes: List[Dict[str, Any]],
    taxonomy: Optional[List[str]] = None,
    llm_client: Optional[Callable[[str, str], str]] = None,
    max_retries: int = 2,
    g: Optional[nx.DiGraph] = None,
) -> DiagnosisResult:
    """
    Make an LLM call to diagnose the failure based on RootCauseCandidate and evidence nodes.

    Strictly validates output schema against DiagnosisResult, retries on malformed JSON,
    and runs groundedness validation if an execution graph g is provided.
    """
    if taxonomy is None:
        taxonomy = TAXONOMY_LIST

    system_prompt, user_prompt = _build_prompts(candidate, evidence_nodes, taxonomy)

    attempts = 0
    last_error: Optional[Exception] = None

    while attempts <= max_retries:
        attempts += 1
        try:
            if llm_client is not None:
                raw_response = llm_client(system_prompt, user_prompt)
            else:
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                if not api_key:
                    res = _fallback_diagnosis(candidate, evidence_nodes, taxonomy)
                    return validate_groundedness(res, g, candidate=candidate) if g else res
                import anthropic  # type: ignore
                client = anthropic.Anthropic(api_key=api_key)
                resp = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                raw_response = resp.content[0].text

            cleaned_json = _clean_json_response(raw_response)
            data = json.loads(cleaned_json)

            # Validate failure category against taxonomy
            if data.get("failure_category") not in taxonomy:
                data["failure_category"] = taxonomy[0] if taxonomy else "Unknown"

            # Validate Pydantic model
            diagnosis = DiagnosisResult.model_validate(data)

            # Run groundedness validation if graph provided
            if g is not None:
                diagnosis = validate_groundedness(diagnosis, g, candidate=candidate)

            return diagnosis

        except Exception as e:
            last_error = e
            if attempts <= max_retries:
                user_prompt += f"\n\nERROR: Your previous response was invalid: {str(e)}. Please output valid JSON matching the exact schema."

    fallback = _fallback_diagnosis(candidate, evidence_nodes, taxonomy, error_note=str(last_error))
    return validate_groundedness(fallback, g, candidate=candidate) if g else fallback


def _fallback_diagnosis(
    candidate: RootCauseCandidate,
    evidence_nodes: List[Dict[str, Any]],
    taxonomy: List[str],
    error_note: Optional[str] = None,
) -> DiagnosisResult:
    """Fallback diagnosis result when LLM client is unavailable or retries are exhausted."""
    category = "Retrieval" if "retrieval" in candidate.node_id.lower() else "Tool" if "tool" in candidate.node_id.lower() else "Unknown"
    if category not in taxonomy:
        category = taxonomy[0] if taxonomy else "Unknown"

    explanation = f"Root cause candidate '{candidate.node_id}' identified with divergence score {candidate.divergence_score:.2f}."
    if error_note:
        explanation += f" (LLM diagnosis error: {error_note})"

    return DiagnosisResult(
        failure_category=category,
        confidence=0.8,
        root_cause_node_id=candidate.node_id,
        evidence_node_ids=candidate.evidence_node_ids or [candidate.node_id],
        explanation=explanation,
        suggested_fix=SuggestedFix(
            type="prompt_patch",
            target=candidate.node_id,
            diff="Review and patch prompt/tool handling for this node.",
        ),
        grounded=True,
    )
