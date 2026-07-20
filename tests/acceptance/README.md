# tests/acceptance/

Acceptance tests for HYDRA's engines.

An acceptance test states a concrete expectation for an engine: given a defined
input, the engine must produce a defined output. It answers a single question —
does the engine behave as specified?

## Rule

**Each future engine must contain at least one acceptance test.** No engine is
considered complete until it has an acceptance test that defines its expected
behavior.

## Shape of an Acceptance Test

```
Input
  ↓
Expected Output
  ↓
Pass / Fail
```

- **Input** — a concrete, defined input for the engine.
- **Expected Output** — the exact output the engine should produce for that input.
- **Pass / Fail** — the engine passes if its actual output matches the expected
  output, and fails otherwise.

This directory currently defines the *structure* of acceptance tests only. No
test implementation exists yet; tests are added alongside each engine as it is
built.
