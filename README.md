# HYDRA

**HYDRA** is an AI Advertising Operating System — a modular platform for turning
product knowledge into high-performing advertising creative through autonomous
decision-making, structured intelligence, and reproducible prompt engineering.

---

## Mission

Give brands a single, intelligent system that transforms raw product information
into ready-to-ship advertising assets. HYDRA removes the manual guesswork from
creative production by reasoning about products, audiences, and channels, then
producing structured, on-brand output at scale.

## Vision

An advertising operating system that thinks like a strategist, writes like a
copywriter, and ships like an engineer. HYDRA aims to be the connective tissue
between product data and marketing execution — a self-improving engine that
learns which creative decisions drive results and encodes that knowledge for
every future campaign.

## Architecture

HYDRA is organized as a set of cooperating engines, each with a single, clear
responsibility:

| Engine | Responsibility |
| --- | --- |
| **Decision Engine** | Chooses strategy, angle, and creative direction from inputs. |
| **Knowledge Engine** | Stores and retrieves product, brand, and market intelligence. |
| **Prompt Engine** | Generates structured, reproducible prompts for creative models. |
| **Automation Layer** | Delivers output to external channels and orchestrates workflows. |
| **QA Layer** | Validates output against schema, brand, and quality rules. |

Each engine communicates through well-defined interfaces and produces
structured, schema-conformant output. The system is designed to be extended one
engine at a time without destabilizing the whole.

## Development Rules

- **Documentation first.** Structure and intent are defined before implementation.
- **Single responsibility.** Each folder and engine owns one concern.
- **Structured output.** Every stage produces predictable, schema-driven results.
- **Reproducibility.** The same inputs must yield the same decisions and prompts.
- **English + Markdown.** All filenames are English; documentation is Markdown.
- **No premature logic.** Business, prompt, and automation logic are added only
  in their designated milestones — never ahead of the roadmap.
- **Clean, professional formatting.** No placeholder filler; every document is
  written to be read.

## Repository Structure

```
HYDRA/
├── README.md          Project overview (this file)
├── CLAUDE.md          Operational brain (placeholder)
├── HYDRA_SPEC.md      Full system specification
├── ROADMAP.md         Version roadmap
├── CHANGELOG.md       Version history
├── LICENSE            License terms
├── .gitignore         Ignored files
├── docs/              Documentation and design notes
├── system/            Core engine architecture and system definitions
├── knowledge/         Product, brand, and market intelligence
├── prompts/           Prompt templates and prompt-engineering assets
├── automation/        Workflow orchestration and channel delivery
├── data/              Datasets, schemas, and structured records
├── tests/             Test suites and validation harnesses
├── scripts/           Utility and operational scripts
├── examples/          Reference usage and sample runs
└── assets/            Static assets and media
```

Each folder contains its own `README.md` describing its purpose in detail.
