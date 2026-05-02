---
name: harden-mode
description: "Use for stabilization, tests, performance control, security checks, and production readiness."
argument-hint: "Describe hardening scope and release criteria"
agent: "Orchestrator"
---
# Harden Mode

Use this mode to prepare production-quality delivery.

## Flow
1. Research: confirm changes and risks.
2. Planning: validation plan with quality gates.
3. Implementation: robustness and predictability improvements.
4. Verification Loop: run build, tests, and performance checks.
5. Review Gate: approve security, cost, and reliability.
6. Release: ship only with gate evidence.

## Guardrails
- Input: acceptance and rollback criteria.
- During execution: validate dependency and integration impact.
- Output: clean build, minimum tests, no performance regression.
