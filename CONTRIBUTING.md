# Contributing to LightEd

## Branching

| Branch        | Purpose                                  |
| ------------- | ---------------------------------------- |
| `main`        | Production. Protected. Deploys to prod.  |
| `develop`     | Integration. All PRs target this branch. |
| `feature/*`   | New features (e.g. `feature/ai-tutor`)   |
| `fix/*`       | Bug fixes                                |
| `chore/*`     | Tooling, docs, infra                     |

Always branch from `develop`:

```bash
git checkout develop
git pull
git checkout -b feature/your-feature
```

## Commit messages (Conventional Commits)

```
<type>(<scope>): <short summary>

[optional body]
[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`.
Scopes: `web`, `api`, `ai`, `infra`, `docs`.

Examples:
- `feat(api): add JWT refresh endpoint`
- `feat(ai): implement weak-topic detection`
- `fix(web): correct progress chart tooltip`

## Pull requests

1. Keep PRs small and focused (one feature/fix).
2. Fill in the PR template.
3. Ensure CI is green (lint, typecheck, tests).
4. Request at least one review.
5. Squash-merge into `develop`.

## Code style

- **Frontend:** ESLint + Prettier, strict TypeScript.
- **Backend/AI:** `ruff` for lint/format, `black`-compatible style, type hints everywhere.
- Never commit secrets — use `.env` (git-ignored).
