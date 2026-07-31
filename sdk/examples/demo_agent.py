"""
TraceMind Live Demo Agent Script.

Simulates all 3 failure pattern scenarios live using the TraceMind Python SDK:
1. retrieval_failure    - Customer support agent retrieves stale 2023 refund policy
2. tool_failure         - Coding agent receives truncated lint output due to rate limits
3. coordination_failure - Multi-agent research system enters a delegation loop

Usage:
    python demo_agent.py --scenario retrieval_failure
    python demo_agent.py --scenario tool_failure
    python demo_agent.py --scenario coordination_failure
    python demo_agent.py --all
"""

import argparse
from pathlib import Path
import sys
import time
from typing import Optional

# Ensure sdk directory is in sys.path
sdk_dir = Path(__file__).resolve().parent.parent
if str(sdk_dir) not in sys.path:
    sys.path.insert(0, str(sdk_dir))

import tracemind as tm


def run_retrieval_failure_scenario(backend_url: str) -> str:
    print("\n🔍 Scenario 1: Live Retrieval Failure (Stale Policy)")
    print("-----------------------------------------------------")

    with tm.Session(
        name="Retrieval Failure — Stale Refund Policy",
        description="Support agent answers using last year's policy.",
        backend_url=backend_url,
    ) as session:
        print(" -> Emitting planning event...")
        session.emit(
            "planning",
            content="Customer asks: 'I bought a laptop 45 days ago and it's defective. Can I get a refund?'",
        )
        time.sleep(0.4)

        print(" -> Calling search_knowledge_base tool...")
        session.emit(
            "tool_call",
            content="search_knowledge_base(query='current refund policy electronics')",
            metadata={
                "tool_name": "search_knowledge_base",
                "latency_ms": 850,
                "relevance_score": 0.42,
                "document_id": "policy-refund-2023-v2",
                "document_date": "2023-03-15",
                "note": "Stale document — 2023 policy retrieved instead of 2025",
            },
        )
        time.sleep(0.6)

        print(" -> Receiving observation...")
        session.emit(
            "observation",
            content="Retrieved document: 'Refund Policy (Effective March 2023) — Electronics returns within 30 calendar days only. No exceptions.'",
            metadata={"source": "policy-refund-2023-v2", "char_count": 210},
        )
        time.sleep(0.3)

        print(" -> Reasoning step...")
        session.emit(
            "reasoning",
            content="The refund policy states a 30-day return window. Customer purchased 45 days ago, so request must be denied.",
            metadata={"latency_ms": 280},
        )
        time.sleep(0.4)

        print(" -> Final answer...")
        session.emit(
            "final_answer",
            content="I'm sorry, but I'm unable to process a refund for your Dell XPS 15 laptop. Our policy allows returns within 30 days, and purchase was 45 days ago.",
            metadata={"correct_answer": "APPROVE refund — 2025 policy allows 60-day returns for defective electronics."},
        )

    print(f"✅ Session finished: {session.session_id}")
    return session.session_id


def run_tool_failure_scenario(backend_url: str) -> str:
    print("\n🛠️  Scenario 2: Live Tool Failure (Truncated Output)")
    print("---------------------------------------------------")

    with tm.Session(
        name="Tool Failure — Truncated Lint Output",
        description="Coding agent receives truncated lint results due to rate limiting.",
        backend_url=backend_url,
    ) as session:
        print(" -> Emitting planning event...")
        session.emit(
            "planning",
            content="Task: Find and fix NullPointerException in UserService.java",
        )
        time.sleep(0.4)

        print(" -> Calling lint_analyze tool...")
        session.emit(
            "tool_call",
            content="lint_analyze(file='src/main/java/com/app/service/UserService.java')",
            metadata={
                "tool_name": "lint_analyze",
                "latency_ms": 12000,
                "error": "rate_limit_degraded",
                "response_truncated": True,
                "response_completeness": 0.45,
            },
        )
        time.sleep(0.8)

        print(" -> Receiving truncated observation...")
        session.emit(
            "observation",
            content="Lint output lines 1-52: UserService constructor DI clean [END OF RESULTS]",
            metadata={"char_count": 290, "note": "Truncated before getUserById method at line 78"},
        )
        time.sleep(0.4)

        print(" -> Reasoning on partial data...")
        session.emit(
            "reasoning",
            content="UserService.java looks clean in lint analysis. The NPE must originate from UserController.java.",
            metadata={"latency_ms": 340},
        )
        time.sleep(0.4)

        print(" -> Final wrong answer...")
        session.emit(
            "final_answer",
            content="Fix: Add null check in UserController.java before returning ResponseEntity.ok(user).",
            metadata={"correct_answer": "Actual bug is in UserService.getUserById() at line 78"},
        )

    print(f"✅ Session finished: {session.session_id}")
    return session.session_id


def run_coordination_failure_scenario(backend_url: str) -> str:
    print("\n🔄 Scenario 3: Live Coordination Failure (Delegation Loop)")
    print("-----------------------------------------------------------")

    with tm.Session(
        name="Coordination Failure — Delegation Loop",
        description="Multi-agent research system enters an unresolved delegation loop.",
        backend_url=backend_url,
    ) as session:
        print(" -> Emitting initial plan...")
        session.emit("planning", content="Task: Produce Q3 competitor pricing report.")
        time.sleep(0.3)

        print(" -> Delegating to ResearchAgent...")
        session.emit(
            "delegation",
            content="Delegating to ResearchAgent: Gather pricing data for AWS, GCP, Azure",
            metadata={"delegated_to": "ResearchAgent"},
            agent_id="ResearchAgent",
        )
        time.sleep(0.5)

        print(" -> ResearchAgent needs market context...")
        session.emit(
            "observation",
            content="ResearchAgent returned partial data: Azure pricing requires market analysis context before normalization.",
            metadata={"source_agent": "ResearchAgent", "latency_ms": 14000, "completeness": 0.6, "flag": "needs_market_context"},
            agent_id="ResearchAgent",
        )
        time.sleep(0.4)

        print(" -> Delegating to AnalysisAgent...")
        session.emit(
            "delegation",
            content="Delegating to AnalysisAgent: Perform market segment analysis for cloud compute",
            metadata={"delegated_to": "AnalysisAgent"},
            agent_id="AnalysisAgent",
        )
        time.sleep(0.5)

        print(" -> AnalysisAgent needs raw pricing data...")
        session.emit(
            "observation",
            content="AnalysisAgent returned: Cannot perform market analysis without complete raw pricing data.",
            metadata={"source_agent": "AnalysisAgent", "latency_ms": 13000, "completeness": 0.0, "flag": "needs_pricing_data"},
            agent_id="AnalysisAgent",
        )
        time.sleep(0.4)

        print(" -> Delegation cycle iteration 2...")
        session.emit(
            "delegation",
            content="Re-delegating to ResearchAgent (Iter 2): Provide raw Azure numbers without normalization.",
            metadata={"delegated_to": "ResearchAgent", "cycle_iteration": 2},
            agent_id="ResearchAgent",
        )
        time.sleep(0.5)

        print(" -> Execution timeout...")
        session.emit(
            "observation",
            content="TIMEOUT: Agent execution exceeded maximum 60s time limit without producing final answer.",
            metadata={"error": "execution_timeout", "cycle_detected": True, "total_delegations": 4},
        )

    print(f"✅ Session finished: {session.session_id}")
    return session.session_id


def main():
    parser = argparse.ArgumentParser(description="TraceMind Live Demo Agent Launcher")
    parser.add_argument(
        "--backend",
        default="http://localhost:8000",
        help="TraceMind backend URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--scenario",
        choices=["retrieval_failure", "tool_failure", "coordination_failure"],
        help="Run a specific scenario",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all three scenarios sequentially",
    )

    args = parser.parse_args()

    if not args.scenario and not args.all:
        parser.print_help()
        sys.exit(1)

    print("🧠 TraceMind Live Agent Simulator")
    print(f"Target Backend: {args.backend}")

    if args.all or args.scenario == "retrieval_failure":
        run_retrieval_failure_scenario(args.backend)

    if args.all or args.scenario == "tool_failure":
        run_tool_failure_scenario(args.backend)

    if args.all or args.scenario == "coordination_failure":
        run_coordination_failure_scenario(args.backend)

    print("\n🎉 Demo agent run complete! Check TraceMind UI or backend GET /sessions endpoint.")


if __name__ == "__main__":
    main()
