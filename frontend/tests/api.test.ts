import assert from "node:assert";
import { test } from "node:test";
import {
  diagnoseTrace,
  generateRegressionTest,
  getTrace,
  getTraces,
} from "../lib/api";
import {
  mockDiagnoseTrace,
  mockGenerateRegressionTest,
  mockGetTrace,
  mockGetTraces,
} from "../lib/mock-api";

// Set environment variable to test mock adapter layer
process.env.NEXT_PUBLIC_USE_MOCK_API = "true";

test("API - getTraces() returns all 3 trace summaries", async () => {
  const summaries = await getTraces();
  assert.strictEqual(summaries.length, 3);
  assert.deepStrictEqual(
    summaries.map((s) => s.id),
    ["retrieval_failure", "tool_failure", "coordination_failure"]
  );
});

test("API - getTrace(id) fetches trace details by ID", async () => {
  const trace = await getTrace("retrieval_failure");
  assert.strictEqual(trace.id, "retrieval_failure");
  assert.strictEqual(trace.expected_failure_category, "Retrieval");
  assert.strictEqual(trace.nodes.length, 9);
});

test("API - diagnoseTrace(id) returns diagnosis and graph elements", async () => {
  const res = await diagnoseTrace("retrieval_failure");
  assert.strictEqual(res.diagnosis.failure_category, "Retrieval");
  assert.strictEqual(res.diagnosis.root_cause_node_id, "node_2");
  assert.strictEqual(res.diagnosis.grounded, true);
  assert.ok(res.diagnosis.confidence > 0 && res.diagnosis.confidence <= 1);
  assert.ok(Array.isArray(res.graph.nodes));
  assert.ok(Array.isArray(res.graph.edges));
});

test("API - generateRegressionTest(id) produces schema-compliant regression spec", async () => {
  const spec = await generateRegressionTest("retrieval_failure");
  assert.strictEqual(spec.trace_id, "retrieval_failure");
  assert.strictEqual(spec.failure_category, "Retrieval");
  assert.strictEqual(spec.root_cause_node_id, "node_2");
  assert.ok(spec.minimal_inputs);
  assert.ok(spec.assertion);
});

test("API - Mock and real API adapters expose matching signatures", async () => {
  const mockSummaries = await mockGetTraces();
  const apiSummaries = await getTraces();
  assert.strictEqual(mockSummaries.length, apiSummaries.length);

  const mockTrace = await mockGetTrace("tool_failure");
  const apiTrace = await getTrace("tool_failure");
  assert.strictEqual(mockTrace.id, apiTrace.id);

  const mockDiag = await mockDiagnoseTrace("coordination_failure");
  const apiDiag = await diagnoseTrace("coordination_failure");
  assert.strictEqual(mockDiag.diagnosis.failure_category, apiDiag.diagnosis.failure_category);

  const mockReg = await mockGenerateRegressionTest("tool_failure");
  const apiReg = await generateRegressionTest("tool_failure");
  assert.strictEqual(mockReg.trace_id, apiReg.trace_id);
});

test("API - Throws readable error on unknown trace ID", async () => {
  await assert.rejects(
    async () => {
      await getTrace("unknown_id");
    },
    (err: Error) => {
      return err.message.includes("not found");
    }
  );
});
