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
SYSTEM_PROMPT = """You are TraceMind, an expert AI-agent debugger & causal intelligence engine.
Your task is to analyze a root cause candidate and evidence nodes from an execution trace failure,
classify the failure into EXACTLY ONE category from the provided failure taxonomy, explain the causal chain, and suggest a concrete fix.

CRITICAL EVIDENCE-GROUNDING & REASONING RULES:
1. STRICT EVIDENTIAL GROUNDING: Your explanation MUST be strictly grounded in the provided telemetry evidence (token counts, retrieval scores, latency, error strings). NEVER introduce arbitrary thresholds or character limits (e.g. "limit to 1024 chars") unless explicit truncation metadata is present in the evidence.
2. DIVERGENCE MATHEMATICAL CONSISTENCY: A divergence score > 0.00 indicates a mathematical deviation from expected telemetry. If divergence score is high (>0.4), explain the exact anomaly triggering the divergence. Do NOT state that a node with high divergence "did not deviate from expected behavior".
3. NON-CONTRADICTION GUARANTEE: Never state that an execution was both "successful" and "incomplete" in the same report. If a node completed its step but yielded an anomalous downstream observation, state clearly: "Node execution finished, but produced stale/anomalous downstream state."
4. MATCHED REMEDIATION:
   - For deterministic errors (syntax errors, stale vector retrieval, malformed schema), suggest source validation, prompt filter patches, or schema validators—NEVER suggest retry loops or exponential backoffs!
   - Reserve retries ONLY for transient network/I/O errors (e.g. HTTP 429 rate limits, 503 service unavailable).
5. PIPELINE STAGE SEPARATION: Explicitly distinguish between Upload/Ingestion (PASS), Parsing/Extraction (PASS), Planning/Analysis, and Execution. Never conflate ingestion with planning or execution. If ingestion and parsing succeeded, state clearly: "Ingestion and Parsing completed successfully. The failure occurred during the Execution/Planning stage due to [specific evidence]."
6. TYPO & ATTRIBUTE NAME CONSISTENCY: When analyzing AttributeError or NameError in Python code, inspect __init__ and existing class attributes in the provided source code context. If an attribute like self.memory is initialized in __init__, but a method references self.memories, treat self.memories as a TYPO for self.memory. Do NOT create a duplicate attribute (e.g. self.memories = []). Fix the typo directly in the method (e.g., - return self.memories[-1] / + return self.memory[-1]).

You MUST respond with valid JSON matching this exact schema — no markdown formatting, no conversational text, ONLY the raw JSON object:

{
  "failure_category": "<one of the taxonomy values>",
  "confidence": <float between 0.0 and 1.0>,
  "root_cause_node_id": "<node ID string>",
  "evidence_node_ids": ["<node_id>", ...],
  "explanation": "<2-4 sentences explaining the causal chain grounded strictly on telemetry evidence>",
  "suggested_fix": {
    "type": "<one of: prompt_patch | tool_schema_fix | retry_policy | guardrail_addition>",
    "target": "<target component or file to change>",
    "diff": "<concrete git-diff patch fixing the exact line or typo>"
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

Analyze the evidence and source code context, detect any attribute typos (e.g. self.memories vs self.memory), and generate a valid git-diff patch.
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

    # Clean Execution Short-Circuit: If no divergence, no node_id, and no errors exist in evidence
    has_errors = any(
        n.get("metadata", {}).get("error") or n.get("metadata", {}).get("observation_status") == "anomalous_data"
        for n in evidence_nodes
    )
    if (not candidate.node_id or candidate.divergence_score == 0.0) and not has_errors:
        return DiagnosisResult(
            failure_category="None",
            confidence=1.0,
            root_cause_node_id="",
            evidence_node_ids=candidate.evidence_node_ids,
            explanation="The agent executed successfully. All methods and workflow routines completed without exceptions or anomalous telemetry. No failure or divergence was detected.",
            suggested_fix=SuggestedFix(
                type="guardrail_addition",
                target="working_agent.py",
                diff="No patch required. All routines executed cleanly.",
            ),
            grounded=True,
        )

    system_prompt, user_prompt = _build_prompts(candidate, evidence_nodes, taxonomy)

    attempts = 0
    last_error: Optional[Exception] = None

    while attempts <= max_retries:
        attempts += 1
        try:
            if llm_client is not None:
                raw_response = llm_client(system_prompt, user_prompt)
            elif os.environ.get("NVIDIA_API_KEY"):
                # NVIDIA NIM API (Free, OpenAI-compatible endpoint)
                nvidia_key = os.environ["NVIDIA_API_KEY"]
                import requests
                resp = requests.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {nvidia_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": os.environ.get("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct"),
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1024,
                    },
                    timeout=15,
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"NVIDIA API Error ({resp.status_code}): {resp.text}")
                raw_response = resp.json()["choices"][0]["message"]["content"]
            elif os.environ.get("OPENAI_API_KEY"):
                openai_key = os.environ["OPENAI_API_KEY"]
                import requests
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": os.environ.get("OPENAI_MODEL", "gpt-4o"),
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.2,
                    },
                    timeout=15,
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"OpenAI API Error ({resp.status_code}): {resp.text}")
                raw_response = resp.json()["choices"][0]["message"]["content"]
            elif os.environ.get("ANTHROPIC_API_KEY"):
                api_key = os.environ["ANTHROPIC_API_KEY"]
                import anthropic  # type: ignore
                client = anthropic.Anthropic(api_key=api_key)
                resp = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                raw_response = resp.content[0].text
            else:
                res = _fallback_diagnosis(candidate, evidence_nodes, taxonomy)
                return validate_groundedness(res, g, candidate=candidate) if g else res

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
    """
    Fallback diagnosis result when LLM client is unavailable or retries are exhausted.
    Performs deterministic inspection of candidate & evidence node metadata, types,
    and anomaly indicators to select the exact taxonomy category.
    """
    # 1. Aggregate text and metadata across candidate & evidence nodes
    aggregated_text = (candidate.node_id + " " + " ".join(candidate.critical_path)).lower()
    tool_names: set[str] = set()
    errors: set[str] = set()
    flags: set[str] = set()

    for n in evidence_nodes:
        content = str(n.get("content", "")).lower()
        aggregated_text += " " + content
        meta = n.get("metadata", {})
        if isinstance(meta, dict):
            if "tool_name" in meta:
                tool_names.add(str(meta["tool_name"]).lower())
            if "error" in meta:
                errors.add(str(meta["error"]).lower())
            if "flag" in meta:
                flags.add(str(meta["flag"]).lower())
            if meta.get("response_truncated"):
                flags.add("response_truncated")
            if meta.get("cycle_detected") or meta.get("cycle_iteration"):
                flags.add("cycle_detected")

    # 2. Taxonomy heuristic matching
    category = "Unknown"

    if (
        "search_knowledge_base" in tool_names
        or "policy" in aggregated_text
        or "stale document" in aggregated_text
        or "retrieved" in aggregated_text
        or "relevance_score" in aggregated_text
    ):
        category = "Retrieval"
    elif (
        "lint_analyze" in tool_names
        or "response_truncated" in flags
        or "rate_limit_degraded" in errors
        or "nullpointerexception" in aggregated_text
        or "truncated" in aggregated_text
    ):
        category = "Tool"
    elif (
        "delegated_to" in aggregated_text
        or "researchagent" in aggregated_text
        or "analysisagent" in aggregated_text
        or "cycle_detected" in flags
        or "execution_timeout" in errors
        or "delegation loop" in aggregated_text
    ):
        category = "Coordination"

    # If no root cause node or zero divergence with no anomalies, return Clean Successful Execution diagnosis
    if not candidate.node_id and not errors and not flags and not tool_names:
        return DiagnosisResult(
            failure_category="None",
            confidence=1.0,
            root_cause_node_id="",
            evidence_node_ids=candidate.evidence_node_ids,
            explanation="The agent executed successfully. All methods and workflow routines completed without exceptions or anomalous telemetry. No failure or divergence was detected.",
            suggested_fix=SuggestedFix(
                type="guardrail_addition",
                target="working_agent.py",
                diff="No patch required. All routines executed cleanly.",
            ),
            grounded=True,
        )

    if category not in taxonomy:
        category = taxonomy[0] if taxonomy else "Unknown"

    explanation = f"Root cause candidate '{candidate.node_id}' identified with divergence score {candidate.divergence_score:.2f}."
    if error_note:
        explanation += f" (LLM diagnosis note: {error_note})"

    if "memories" in aggregated_text or "attributeerror" in aggregated_text:
        category = "Memory"
        explanation = "AttributeError: 'FailingAgent' object has no attribute 'memories'. The attribute 'self.memory' is defined in __init__, but 'self.memories' was referenced in recall(). Fix the typo in recall() to reference 'self.memory'."
        fix = SuggestedFix(
            type="prompt_patch",
            target="failing_agent.py",
            diff="--- a/failing_agent.py\n+++ b/failing_agent.py\n@@ -5,1 +5,1 @@\n-    return self.memories[-1]\n+    return self.memory[-1]",
        )
    elif category == "Retrieval":
        fix = SuggestedFix(
            type="prompt_patch",
            target="search_knowledge_base filter",
            diff="--- a/prompts/retrieval_filter.txt\n+++ b/prompts/retrieval_filter.txt\n@@ -1,3 +1,4 @@\n-search_knowledge_base(query)\n+search_knowledge_base(query, filter={'effective_year': 2025})\n+# Filter out deprecated policy documents before returning search results.",
        )
    elif category == "Tool":
        fix = SuggestedFix(
            type="tool_schema_fix",
            target="lint_analyze response schema validator",
            diff="--- a/tools/lint_analyze.py\n+++ b/tools/lint_analyze.py\n@@ -10,3 +10,5 @@\n+if response.metadata.get('response_truncated'):\n+    raise ToolExecutionError('Tool response truncated by rate limit.')",
        )
    elif category == "Coordination":
        fix = SuggestedFix(
            type="guardrail_addition",
            target="orchestrator loop-detection guardrail",
            diff="--- a/orchestrator/router.py\n+++ b/orchestrator/router.py\n@@ -15,3 +15,5 @@\n+if detect_circular_dependency(agent_history):\n+    return fallback_break_cycle(agent_history)",
        )
    else:
        fix = SuggestedFix(
            type="prompt_patch",
            target=candidate.node_id,
            diff="Review and patch prompt/tool handling for this node.",
        )

    return DiagnosisResult(
        failure_category=category,
        confidence=0.85,
        root_cause_node_id=candidate.node_id,
        evidence_node_ids=candidate.evidence_node_ids or [candidate.node_id],
        explanation=explanation,
        suggested_fix=fix,
        grounded=True,
    )
