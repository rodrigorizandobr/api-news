---
name: review-gate
description: "Use to run final release gate with quality, performance, security, and cost approval checkpoints."
argument-hint: "Provide the task and validation artifacts"
agent: "Orchestrator"
---
# Review Gate

Run the final gate before release.

## Checklist
1. Build with no errors.
2. Minimum tests executed for impacted scope.
3. No relevant mobile performance regression.
4. No open critical security risk.
5. Cost impact identified and accepted.

## Output
- Gate status: Approved or Blocked.
- Evidence by criterion.
- Residual risks and mitigation plan.
