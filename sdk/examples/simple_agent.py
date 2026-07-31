"""
Simple Agent Example using TraceMind Python SDK.

Demonstrates minimal 5-line agent instrumentation.
"""

from pathlib import Path
import sys
import time

# Ensure sdk directory is in sys.path
sdk_dir = Path(__file__).resolve().parent.parent
if str(sdk_dir) not in sys.path:
    sys.path.insert(0, str(sdk_dir))

import tracemind as tm


def run_simple_agent():
    print("🚀 Starting Simple Agent with TraceMind instrumentation...")

    with tm.Session(name="Simple Math Assistant", backend_url="http://localhost:8000") as session:
        session.emit("planning", content="Task: Calculate mortgage payment for $500k loan at 6.5% interest.")
        time.sleep(0.3)

        session.emit(
            "tool_call",
            content="calculator(principal=500000, rate=0.065, years=30)",
            metadata={"tool_name": "calculator"},
        )
        time.sleep(0.5)

        session.emit(
            "observation",
            content="Result: $3,160.34 monthly payment",
            metadata={"source": "calculator_tool"},
        )
        time.sleep(0.3)

        session.emit("reasoning", content="Payment calculated as $3,160.34 per month including principal and interest.")
        time.sleep(0.2)

        session.emit(
            "final_answer",
            content="The estimated monthly mortgage payment for a $500,000 loan at 6.5% interest over 30 years is $3,160.34.",
        )

    print("✅ Session complete! TraceMind session ID:", session.session_id)


if __name__ == "__main__":
    run_simple_agent()
