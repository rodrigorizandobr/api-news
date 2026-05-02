---
name: bugfix
description: Bugfix
argument-hint: "Describe the bug and context"
agent: "agent"
---

# Bugfix Workflow (/bugfix)

// turbo-all
This workflow follows **Research -> Planning -> Implementation** with verification loops and resilience against stuck processes.

## Trigger
Use this flow whenever a critical bug is reported or detected during development.

## Phase 1: Research
The goal is to find root cause without assumptions.

1. **Investigate Logs**:
- Analyze `storage/logs/app.log` and `storage/logs/audit.log` for exceptions.
- Check for permission or I/O failures in `/storage`.
- Check frontend build console logs when frontend is involved.
- Check request and browser console errors.
2. **Reproduction**:
- Reproduce the bug with a new unit or E2E test.
- Reproduce adjacent scenarios (unit/integration/E2E/exploratory) for the same feature.
- **Treatment Proof**: if `open_browser_url` hangs (>30s), stop execution, clear browser cache, and inspect backend logs immediately.
3. **Architecture Analysis**:
- Check whether the bug violates `backend.md` or `frontend.md` principles.

## Phase 2: Planning
Create a robust plan before touching code.

1. **Document Solution**: update `implementation_plan.md`.
2. **Define Tests**: list exactly which tests must pass for bug extinction.
3. **Zero-Mock Policy**: use real environment when possible (except external APIs such as OpenAI).
4. Planning must include code-quality checks, passing tests, minimum coverage, reference architecture, best practices, and security.
5. Always ensure frontend build runs with zero errors/warnings.
6. Always ensure backend build/start runs with zero errors/warnings.

## Phase 3: Implementation & Verification Loop
Execute with full quality guarantees.

0. **Environment Validation**:
- Before coding, validate `PYTHONPATH` and storage paths.
- In local environment, ensure Datastore Emulator is running.
1. **Execute Change**: apply code patches following SOLID.
2. **Infinite Correction Loop**:
- **Step A**: run build (`npm run build` or equivalent). If it fails, return to code.
- **Step B**: run unit and integration tests (85%+ backend coverage target).
- **Step C**: run E2E tests (Playwright, 80%+ frontend coverage target).
- **Step D**: inspect logs. No new `WARNING` or `ERROR` in `/storage/logs`.
- **Step E**: if any step fails, return to **Phase 2 (Planning)** and iterate. The flow ends only with full success.

## Resilience Rules

1. **Active Monitoring**: never run background commands for more than 2 minutes without checking status.
2. **Browser Timeout**: if `read_browser_page` (or similar) hangs, use `send_command_input` to kill zombie backend processes.
3. **Log Cleanliness**: clean logs before final verification to avoid false positives from old errors.

## Definition of Done (DoD)
- [ ] Bug reproduced and resolved.
- [ ] Automated tests passing (Unit, Integration, E2E).
- [ ] Minimum coverage reached (85% backend, 80% frontend).
- [ ] Zero error/warning logs generated during verification.
- [ ] Documentation (`walkthrough.md`) updated with fix evidence.
