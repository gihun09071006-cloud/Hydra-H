# HYDRA Story Engine (SGE) — Specification

## Purpose

The **Story Generation Engine (SGE)** transforms a selected Creative Strategy
into a structured short-form video **storyboard**. It turns the chosen strategy,
hook, story pattern, and CTA into an ordered sequence of scenes that carry a
complete narrative — Hook through Call To Action.

The SGE defines *narrative structure only*. It does **not** implement business
logic, write prompts, or include camera or production wording. This document is
a specification only.

### Relationship to existing engines (no duplicate architecture)

No equivalent specification existed. The SGE occupies a distinct stage between
strategy selection and prompt compilation:

| Concern | Owner |
| --- | --- |
| Selecting the strategy, hook, story pattern, CTA | Creative Strategy Engine (`CREATIVE_STRATEGY_ENGINE.md`) |
| **Turning that strategy into a phased scene storyboard** | **Story Engine (this doc)** |
| Compiling scenes into prompts | Prompt Compiler (future, `PROMPT_CREATED` state) |
| Ordering the pipeline and enforcing phases via state | State Machine (`STATE_MACHINE.md`) |

The SGE **realizes** the State Machine's `STORY_CREATED` (the phased narrative)
and `SCENES_CREATED` (the ordered scene set) states, and its output is the input
to `PROMPT_CREATED`.

---

## Inputs

### Input 1 — Creative Strategy Output

The Creative Strategy Engine output (`system/CREATIVE_STRATEGY_ENGINE.md`):
`strategy`, `hook_type`, `story_pattern`, and `cta_style`. The SGE adopts the
given `story_pattern` and expresses `hook_type` in the Hook phase and `cta_style`
in the CTA phase.

### Input 2 — Product Intelligence JSON

The canonical Product Intelligence Record
(`data/schemas/product_intelligence.schema.json`, documented in
`docs/PRODUCT_INTELLIGENCE.md`). Scene goals and descriptions draw on its fields:
`pain_analysis` (Problem), `functional_analysis` / `usp` (Solution),
`visual_analysis` / `competitive_analysis` (Proof), and `customer_analysis` for
tone and audience.

---

## Outputs

The engine emits a storyboard object:

```json
{
  "story_pattern": "",
  "duration": 20,
  "scenes": [
    {
      "scene": 1,
      "duration": 2,
      "goal": "",
      "description": ""
    }
  ]
}
```

| Field | Type | Description |
| --- | --- | --- |
| `story_pattern` | string | The story pattern carried over from the Creative Strategy Output. |
| `duration` | integer (seconds) | Total storyboard duration. Default 20. |
| `scenes` | array | The ordered scenes (see **Scene Rules**). |
| `scenes[].scene` | integer | Scene number, ordered from 1. |
| `scenes[].duration` | integer (seconds) | Scene length; scene durations sum to `duration`. |
| `scenes[].goal` | string | The scene's narrative goal, mapping to one of the five phases. |
| `scenes[].description` | string | Narrative description of what happens — structure only, no camera or prompt wording. |

---

## Story Rules

Every story MUST contain these five phases, in order:

1. **Hook**
2. **Problem**
3. **Solution**
4. **Proof**
5. **Call To Action**

**No phase may be skipped.** Each phase is realized by one or more scenes; every
phase must be represented by at least one scene, and the scenes preserve the
phase order above.

---

## Scene Rules

Each scene MUST define:

- **Duration** — the scene's length in seconds.
- **Goal** — the narrative purpose of the scene (which phase it serves).
- **Description** — what happens in the scene, as narrative structure.

Each scene MUST NOT contain:

- **No camera instructions** (shots, angles, movement).
- **No prompt wording** (model-facing phrasing).
- **Only narrative structure.**

---

## Timing Rules

Default total duration: **20 seconds**.

Recommended phase distribution:

| Phase | Recommended window |
| --- | --- |
| Hook | 0–3 sec |
| Problem | 3–7 sec |
| Solution | 7–14 sec |
| Proof | 14–18 sec |
| CTA | 18–20 sec |

These are **recommendations, not hard rules**. The distribution may be adjusted
per product and strategy, provided all five phases remain present and ordered and
the scene durations sum to the total `duration`.

---

## Story Validation

Before a storyboard is emitted, the engine validates that every phase exists:

- Hook exists
- Problem exists
- Solution exists
- Proof exists
- CTA exists

**If any phase is missing, the engine returns a validation failure** (it does not
emit an incomplete storyboard). This maps directly to the State Machine's
`STORY_CREATED` failure condition, which triggers that state's retry / fallback
logic.

---

## Story Flow

```
Creative Strategy Output ─┐
                          ├─►  SGE
Product Intelligence JSON ┘     │
                                ▼
        1. Adopt story_pattern; plan the five phases
                                ▼
        2. Allocate scenes across phases (Hook→Problem→Solution→Proof→CTA)
                                ▼
        3. For each scene: set duration, goal (phase), description
                                ▼
        4. Validate all five phases exist  ──►  missing? return validation failure
                                ▼ (valid)
             Output { story_pattern, duration, scenes[] }
```

---

## Validation Rules (summary)

| Rule | Requirement |
| --- | --- |
| Phase completeness | All five phases (Hook, Problem, Solution, Proof, CTA) present. |
| Phase order | Scenes preserve Hook → Problem → Solution → Proof → CTA order. |
| Scene fields | Every scene has duration, goal, and description. |
| No production wording | No camera instructions or prompt phrasing in any scene. |
| Duration consistency | Scene durations sum to the total `duration`. |

A failure of any rule returns a validation failure rather than a storyboard.

---

## Future Extension Points

- **Explicit `phase` field per scene.** Add a `phase` enum to each scene so phase
  coverage is validated structurally rather than inferred from `goal`.
- **Variable durations.** Support total durations other than 20 seconds with
  proportional phase windows.
- **Multiple scenes per phase.** Formalize how phases expand into several scenes
  for longer or more detailed stories.
- **Pattern-specific templates.** Per-`story_pattern` scene templates, added
  centrally without changing the output contract.

---

## Relationship Summary

| Engine / Stage | Relationship |
| --- | --- |
| **Creative Strategy Engine** | Provides `story_pattern`, `hook_type`, `cta_style`, `strategy` — the SGE's primary input. |
| **Prompt Compiler** | Consumes the SGE's scene set to produce prompts (`PROMPT_CREATED`). The SGE stops at narrative structure. |
| **State Machine** | The SGE realizes `STORY_CREATED` and `SCENES_CREATED`; validation failures drive their retry / fallback. |

---

## Compatibility

| Requirement | How it is met |
| --- | --- |
| Creative Strategy Engine | Consumes CSE output; carries `story_pattern`, expresses `hook_type` and `cta_style` in their phases. |
| Product Intelligence schema | Scene goals/descriptions draw on canonical fields (`pain_analysis`, `functional_analysis`, `usp`, `visual_analysis`, `competitive_analysis`, `customer_analysis`). |
| State Machine | Realizes `STORY_CREATED` and `SCENES_CREATED`; validation maps to their failure conditions; output feeds `PROMPT_CREATED`. |
| No duplicate architecture | No equivalent spec existed; the SGE fills a distinct role and references, rather than redefines, existing engines. |

---

## Scope Boundary

| In scope | Out of scope |
| --- | --- |
| A phased, ordered scene storyboard | Generating advertisements |
| Scene duration, goal, description | Camera instructions or shot design |
| Phase completeness validation | Writing prompts or prompt wording |
| Feeding the Prompt Compiler | Rendering or delivery |
