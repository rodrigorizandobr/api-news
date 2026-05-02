---
name: dev
description: dev
argument-hint: "Describe the development task"
agent: "agent"
---

# Development Workflow (RPI)

// turbo-all
This workflow guides end-to-end development using the cycle **Research -> Planning -> Implementation**.

## Phase 1: Research
The goal is to deeply understand requirements and ecosystem impact.

1. **Requirement Analysis**: refine stories and tasks proposed by the user.
2. **Technical Research**:
- Check whether similar components already exist in the codebase.
- **Treatment Proof**: if external docs or codebase search appears stalled (>30s), restart using more specific filters.

## Phase 2: Planning
Document and design before coding.

1. **Implementation Plan**: create or update `implementation_plan.md` with component-level changes.
2. **Quality Gates Definition**:
- List tests to create/update.
- Ensure architecture follows SOLID and design patterns.
3. Planning must include code-quality checks, passing tests, minimum coverage, reference architecture, best practices, and security checks.
4. Always ensure frontend build runs with zero errors or warnings.
5. Always ensure backend build/start runs with zero errors or warnings.

## Phase 3: Implementation & Verification Loop
Execute with strict quality guarantees.

0. **Environment Validation**:
- Confirm write permissions for `/storage`.
1. **Development**: implement changes according to the approved plan.
2. **Infinite Correction Loop**:
- **Tests**:
- Unit (80% coverage)
- Integration (80% coverage)
- E2E (50% critical path coverage)
- **Treatment Check**: if the test browser freezes, use `send_command_input` to clean zombie processes and restart the loop.
- If any step fails, return to **Phase 2 (Planning)**, adjust strategy, and repeat. The flow ends only with full success.

## Definition of Done (DoD)
- [ ] Feature implemented and functional.
- [ ] Automated tests passing (Unit, Integration, E2E).
- [ ] Minimum coverage reached and verified.
- [ ] Zero error/warning logs generated.
- [ ] Walkthrough documented with evidence.
