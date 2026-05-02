---
description: "Use when implementing or modifying backend services, APIs, authentication flows, or server-side logic. Enforce Python as the backend language."
applyTo: "api/**/*.py"
---
# Backend Python Rule

- Backend implementation must use Python.
- Prefer FastAPI for HTTP services unless explicitly requested otherwise.
- Keep route handlers thin and move business logic to dedicated modules.
- Add or update tests for new endpoints and critical logic.
- Keep external integrations behind adapter functions for easier mocking and replacement.
- Validate request and response models with Pydantic.
