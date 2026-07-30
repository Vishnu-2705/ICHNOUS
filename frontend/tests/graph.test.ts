import assert from "node:assert";
import { test } from "node:test";
import { toReactFlowElements } from "../lib/graph";
import { SerializedGraph } from "../types/tracemind";

test("Graph - toReactFlowElements converts nodes & highlights root cause", () => {
  const sampleGraph: SerializedGraph = {
    nodes: [
      { id: "node_1", type: "plan", content: "Start" },
      { id: "node_2", type: "tool_call", content: "Stale retrieval" },
      { id: "node_3", type: "observation", content: "Result" },
    ],
    edges: [
      { source: "node_1", target: "node_2" },
      { source: "node_2", target: "node_3" },
    ],
  };

  const diagnosis = {
    failure_category: "Retrieval",
    confidence: 0.88,
    root_cause_node_id: "node_2",
    evidence_node_ids: ["node_2", "node_3"],
    explanation: "Stale retrieval",
    suggested_fix: { type: "prompt_patch", target: "prompt", diff: "" },
    grounded: true,
  };

  const { nodes, edges } = toReactFlowElements(sampleGraph, diagnosis, [], ["node_1", "node_2"]);

  assert.strictEqual(nodes.length, 3);
  assert.strictEqual(edges.length, 2);

  // Check node 2 is marked as root_cause
  const node2 = nodes.find((n) => n.id === "node_2");
  assert.ok(node2);
  assert.strictEqual(node2.data.visualState, "root_cause");

  // Check node 3 is marked as evidence
  const node3 = nodes.find((n) => n.id === "node_3");
  assert.ok(node3);
  assert.strictEqual(node3.data.visualState, "evidence");

  // Check node 1 is marked as critical_path
  const node1 = nodes.find((n) => n.id === "node_1");
  assert.ok(node1);
  assert.strictEqual(node1.data.visualState, "critical_path");
});

test("Graph - Handles empty or missing graph gracefully", () => {
  const emptyRes = toReactFlowElements({ nodes: [], edges: [] });
  assert.strictEqual(emptyRes.nodes.length, 0);
  assert.strictEqual(emptyRes.edges.length, 0);
});
