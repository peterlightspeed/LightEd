# Cross-cutting & E2E Tests

This folder is for tests that span more than one service (e.g. full API + AI
flows, or browser E2E with Playwright).

- Unit tests live next to their code: `apps/api/tests`, `ai/tests`.
- Put integration / end-to-end tests here.

## Planned

```bash
# API + AI integration (Sprint 2)
pytest tests/integration

# Browser E2E (Sprint 4)
npx playwright test
```
