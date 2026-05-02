---
description: "Use when executing any task with the multi-agent orchestration model. Enforce delivery phases, handoff logging, and quality guardrails."
applyTo: "**"
---
# Agent Operations

## Standard Phases
- Research
- Planning
- Implementation
- Verification Loop
- Review Gate
- Release

## Mode Selection
- Vibe Mode: rapid discovery, prototyping, UX, and experimentation.
- Harden Mode: stabilization, tests, performance, security, and cost.
- Every task must start with explicit mode selection.

## Mandatory Guardrails
- Input: minimum requirement + acceptance criteria.
- During execution: validate scope and impact.
- Output: clean build, minimum tests, no performance regression.

## Mandatory Observability
- Handoff log.
- Time per stage.
- Cost per task.
- Rework rate by change type.

## Handoff Discipline
- Handoff is mandatory outside the active specialty.
- Apply checklist in `docs/ai-ops/handoff-checklist.md`.
