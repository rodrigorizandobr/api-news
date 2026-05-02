---
name: delivery-flow
description: "Use as the standard end-to-end workflow for any task: Research, Planning, Implementation, Verification Loop, Review Gate, Release."
argument-hint: "Describe the task and expected result"
agent: "Orchestrator"
---
# Standard Delivery Flow

Apply this flow to any project task.

## Stages
1. Research
- Consolidate technical and product context.
- Define constraints and dependencies.

2. Planning
- Define incremental plan and quality gates.
- Record acceptance criteria and risks.

3. Implementation
- Execute changes with minimum possible impact.
- Enforce handoff when leaving active specialty.

4. Verification Loop
- Run essential scope-based validations.
- If any check fails, return to Planning and iterate.

5. Review Gate
- Consolidate QA, Performance, Security, and Cost findings.
- Block release if critical risk exists.

6. Release
- Publish final summary: decision, residual risks, next steps.

## Mandatory Operational Logs
- Executed handoffs.
- Time by stage.
- Estimated task cost.
- Rework by change type.
