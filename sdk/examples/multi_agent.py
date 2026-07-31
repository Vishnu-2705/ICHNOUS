"""
Multi-Agent Delegation Example using TraceMind Python SDK.

Demonstrates sub-agent delegation tracking with agent_id metadata.
"""

from pathlib import Path
import sys
import time

# Ensure sdk directory is in sys.path
sdk_dir = Path(__file__).resolve().parent.parent
if str(sdk_dir) not in sys.path:
    sys.path.insert(0, str(sdk_dir))

import tracemind as tm


def run_multi_agent():
    print("🤖 Starting Multi-Agent Orchestrator with TraceMind instrumentation...")

    with tm.Session(name="Research & Analysis Multi-Agent Workflow", backend_url="http://localhost:8000") as session:
        # Orchestrator plans task
        session.emit(
            "planning",
            content="Task: Prepare market analysis for AI chips market in 2026.",
            agent_id="orchestrator",
        )
        time.sleep(0.4)

        # Delegate to ResearchAgent
        session.emit(
            "delegation",
            content="Delegating data collection to ResearchAgent",
            metadata={"delegated_to": "ResearchAgent"},
            agent_id="orchestrator",
        )
        time.sleep(0.5)

        # ResearchAgent events
        session.emit(
            "tool_call",
            content="web_search('NVIDIA vs AMD vs Custom ASICs 2026 market share')",
            metadata={"tool_name": "web_search", "relevance_score": 0.92},
            agent_id="ResearchAgent",
        )
        time.sleep(0.6)

        session.emit(
            "observation",
            content="Found dataset: NVIDIA 78%, AMD 12%, Custom Cloud ASICs 10%",
            metadata={"source": "market_reports_2026"},
            agent_id="ResearchAgent",
        )
        time.sleep(0.3)

        # Delegate to AnalysisAgent
        session.emit(
            "delegation",
            content="Delegating share breakdown to AnalysisAgent",
            metadata={"delegated_to": "AnalysisAgent"},
            agent_id="orchestrator",
        )
        time.sleep(0.4)

        # AnalysisAgent events
        session.emit(
            "reasoning",
            content="Custom cloud ASICs growing at 35% CAGR due to hyperscaler internal workloads.",
            agent_id="AnalysisAgent",
        )
        time.sleep(0.3)

        # Orchestrator synthesizes final answer
        session.emit(
            "final_answer",
            content="Market Summary: NVIDIA leads with 78% share, but custom cloud ASICs (Google TPU, AWS Trainium) represent the fastest growing segment at 35% CAGR.",
            agent_id="orchestrator",
        )

    print("✅ Multi-agent session finished! TraceMind session ID:", session.session_id)


if __name__ == "__main__":
    run_multi_agent()
