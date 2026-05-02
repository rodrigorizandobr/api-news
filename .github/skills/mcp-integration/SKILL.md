---
name: mcp-integration
description: "Standardize MCP usage in your project. Use when integrating Firebase/GCP, internal docs, and QA tooling through MCP servers."
---

# MCP Integration Standard

## Goal
Adopt MCP as the standard for tool and context integrations.

## Priority Integrations
1. Firebase and GCP operational tools.
2. Internal project docs.
3. QA and performance tooling interfaces.

## Rules
- Prefer MCP over ad-hoc prompt-based context passing.
- Keep server catalog documented and versioned.
- Validate permission scope before enabling write actions.

## Expected Result
- Fewer long prompts.
- Higher operational consistency.
- Better integration traceability.
