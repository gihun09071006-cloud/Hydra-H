# HYDRA Advertising Decision Engine — Specification

This document specifies **how the HYDRA Advertising Decision Engine makes
decisions**. It defines the reasoning workflow, the structure every decision
must take, and the contracts between steps.

This specification does **not** generate advertisements, does **not** generate
prompts, and contains **no implementation**. It defines decision-making only.

---

## 1. Purpose

The Decision Engine is HYDRA's reasoning core. Given structured product and
market inputs, it produces a **Creative Brief** — a fully-reasoned decision
record that downstream engines (Prompt Engine, Automation) can act on.

The engine's responsibility ends at the brief. It decides *what* should be made
and *why*; it never produces the creative itself.

---

## 2. Decision Principles

Every step in the engine adheres to these principles:

- **Explainability.** No decision is a black box. Each one states its reasoning.
- **Calibrated confidence.** Every decision carries a confidence score.
- **Preserved alternatives.** Rejected options are recorded, not discarded.
- **Impact orientation.** Every decision is tied to an expected business outcome.
- **Reproducibility.** Identical inputs and knowledge produce identical decisions.
- **Traceability.** Each step consumes the previous step's output, forming an
  auditable chain from product understanding to final brief.

---

## 3. Decision Record Structure

Every decision the engine makes — at every step — MUST include the following
four fields. This is the atomic unit of the engine.

| Field | Description |
| --- | --- |
| **Reason** | The rationale behind the decision, grounded in the inputs and knowledge available at this step. |
| **Confidence Score** | A calibrated score expressing how strongly the engine backs this decision (see §3.1). |
| **Alternative Options** | The other viable options that were considered and not selected, each with a short note on why it was set aside. |
| **Expected Business Impact** | The outcome the decision is expected to drive (e.g. relevance, differentiation, conversion), stated in business terms. |

### 3.1 Confidence Score

- Expressed on a normalized scale of **0.0 – 1.0** (or 0–100%).
- Reflects the engine's certainty given input completeness and evidence strength.
- Low-confidence decisions are permitted but MUST surface their uncertainty so
  downstream steps and human reviewers can weigh them appropriately.

### 3.2 Alternative Options

- At minimum, viable rejected options are retained.
- Each alternative records *what it was* and *why it lost*.
- Alternatives preserve optionality: if a winning decision fails downstream QA,
  the next-best option is already documented.

---

## 4. Decision Workflow

The engine executes eight sequential steps. Each step is a decision (or a set of
decisions) that follows the Decision Record Structure in §3. The output of each
step is the input to the next.

```
STEP 1  Understand Product
STEP 2  Understand Customer
STEP 3  Identify Buying Motivation
STEP 4  Select Marketing Strategy
STEP 5  Generate Multiple Creative Concepts
STEP 6  Evaluate Concepts
STEP 7  Select Winner
STEP 8  Generate Creative Brief
```

### STEP 1 — Understand Product

Establish a grounded understanding of what is being advertised.

- **Input:** Raw product information from the Knowledge Engine.
- **Decisions:** Identify the core value proposition, key features, category, and
  differentiators; determine which product attributes are advertising-relevant.
- **Output:** A structured product understanding, with each conclusion carrying
  its Reason, Confidence Score, Alternative Options, and Expected Business Impact.

### STEP 2 — Understand Customer

Define who the advertising is for.

- **Input:** Product understanding (Step 1) plus audience and market knowledge.
- **Decisions:** Identify the target audience segment(s), their context, needs,
  and objections; determine which segment to prioritize.
- **Output:** A structured customer profile, each conclusion as a decision record.

### STEP 3 — Identify Buying Motivation

Determine *why* the customer would buy.

- **Input:** Product understanding (Step 1) and customer profile (Step 2).
- **Decisions:** Identify the primary and secondary purchase drivers (functional,
  emotional, social, situational); rank motivations by strength and relevance.
- **Output:** A prioritized set of buying motivations as decision records.

### STEP 4 — Select Marketing Strategy

Choose the strategic direction that best activates the buying motivation.

- **Input:** Buying motivations (Step 3), product and customer understanding.
- **Decisions:** Select the marketing strategy / angle (e.g. positioning,
  message frame, emphasis) that best matches the top motivations.
- **Output:** A selected strategy as a decision record, with rejected strategies
  retained as Alternative Options.

### STEP 5 — Generate Multiple Creative Concepts

Diverge: produce several distinct creative directions under the chosen strategy.

- **Input:** Selected strategy (Step 4) and all upstream understanding.
- **Decisions:** Define **multiple** candidate creative concepts, each a distinct
  interpretation of the strategy. Concepts are described at the *idea* level
  (angle, hook, core message) — **not** as finished ads or prompts.
- **Output:** A set of candidate concepts, each a decision record explaining why
  it is a valid expression of the strategy.

### STEP 6 — Evaluate Concepts

Judge the candidate concepts against consistent criteria.

- **Input:** Candidate concepts (Step 5).
- **Decisions:** Score each concept on defined evaluation criteria (e.g. strategic
  fit, differentiation, audience resonance, feasibility, expected impact).
- **Output:** A scored, comparable evaluation of every concept, each score
  justified as a decision record.

### STEP 7 — Select Winner

Converge: choose the single concept to move forward.

- **Input:** Concept evaluations (Step 6).
- **Decisions:** Select the winning concept. The Reason cites the evaluation;
  the Alternative Options are the runner-up concepts, preserved for fallback.
- **Output:** One winning concept as a decision record.

### STEP 8 — Generate Creative Brief

Consolidate the full decision chain into a single, actionable brief.

- **Input:** The winning concept (Step 7) and the complete decision trail.
- **Decisions:** Assemble the brief that downstream engines will act on —
  summarizing product, customer, motivation, strategy, and the chosen concept,
  each element traceable to the decision that produced it.
- **Output:** A **Creative Brief**: the engine's final, reasoned deliverable.

---

## 5. Workflow Contract

- Steps run **in order**; each consumes the previous step's output.
- Every step emits decisions in the structure defined in §3 — no exceptions.
- The chain is **auditable end to end**: any element of the final brief can be
  traced back through the steps that produced it.
- The engine's output boundary is the **Creative Brief**. Generation of prompts
  or advertisements is out of scope and handled by other engines.

---

## 6. Scope Boundary

| In scope | Out of scope |
| --- | --- |
| How decisions are made | Generating advertisements |
| The reasoning workflow | Generating prompts |
| The structure of each decision | Any implementation or logic |
| The Creative Brief as output | Channel delivery or automation |
