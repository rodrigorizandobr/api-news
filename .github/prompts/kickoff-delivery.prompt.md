---
name: kickoff-delivery
description: "Use at task start to auto-select Vibe Mode or Harden Mode, assign specialists, and initialize checkpoints."
argument-hint: "Describe task, risk, timeline, and expected impact"
agent: "Orchestrator"
---
# Kickoff Delivery

Start every task with this protocol.

## Step 1: Classify Mode
Select Vibe Mode if:
- scope is still exploratory
- there is UX/product uncertainty
- the goal is to prototype and learn quickly

Select Harden Mode if:
- the task changes critical behavior
- it involves external integration, security, or cost
- it is close to release

## Step 2: Define Mandatory Inputs
- Minimum requirement.
- Acceptance criteria.
- Initial scope and out-of-scope.
- Primary task risk.

## Step 3: Assign Specialists
- Frontend Experience for UI/UX.
- Backend API Specialist for API/integrations.
- QA Performance for validation and regression.
- Security Cost for risk and cost.

## Step 4: Initialize Delivery Flow
- Research -> Planning -> Implementation -> Verification Loop -> Review Gate -> Release.

## Step 5: Initialize Observability
- Open handoff log.
- Record time by stage.
- Estimate task cost.
- Record rework loops when they occur.
