"""Tests for verifying trace fixtures and fixture helpers."""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fixtures import (
    get_all_fixtures,
    get_coordination_failure_trace,
    get_retrieval_failure_trace,
    get_tool_failure_trace,
    load_fixture_json,
)
from models.trace import Trace


def test_fixtures_validation():
    # Test helper function calls
    retrieval_trace = get_retrieval_failure_trace()
    assert isinstance(retrieval_trace, Trace)
    assert retrieval_trace.id == "trace_retrieval"
    assert len(retrieval_trace.nodes) > 0

    tool_trace = get_tool_failure_trace()
    assert isinstance(tool_trace, Trace)
    assert tool_trace.id == "trace_tool"
    assert len(tool_trace.nodes) > 0

    coordination_trace = get_coordination_failure_trace()
    assert isinstance(coordination_trace, Trace)
    assert coordination_trace.id == "trace_coordination"
    assert len(coordination_trace.nodes) > 0

    # Test all fixtures dictionary
    all_fixtures = get_all_fixtures()
    assert len(all_fixtures) == 3
    assert set(all_fixtures.keys()) == {
        "trace_retrieval",
        "trace_tool",
        "trace_coordination",
    }

    # Verify node fields in all traces
    required_node_fields = {
        "id",
        "type",
        "timestamp",
        "content",
        "metadata",
        "reads_from",
    }
    for fixture_name in [
        "retrieval_failure.json",
        "tool_failure.json",
        "coordination_failure.json",
    ]:
        data = load_fixture_json(fixture_name)
        trace_obj = Trace.model_validate(data)
        assert trace_obj.id is not None

        for node in data["nodes"]:
            missing_fields = required_node_fields - set(node.keys())
            assert not missing_fields, f"Node {node.get('id')} in {fixture_name} missing fields: {missing_fields}"

    print("All trace fixtures validated successfully against the Trace model!")


if __name__ == "__main__":
    test_fixtures_validation()
