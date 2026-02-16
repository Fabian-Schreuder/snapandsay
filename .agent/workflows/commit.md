---
description: Automatic commit message generator and fast AI-powered commit for all current changes
---

// turbo-all

This workflow automatically stages all changes, generates a descriptive commit message, and commits them in one go.

### Steps:

1. **Lint & Format Codebase**: Ensure code quality by running formatting and linting for both backend and frontend.
   ```bash
   (cd backend && uv run ruff format . && uv run ruff check .) && (cd frontend && pnpm lint)
   ```
2. **Stage All Changes**: Automatically stage all modified and new files.
   ```bash
   git add .
   ```
3. **Analyze Changes**: Get the diff of staged changes to understand the context.
   ```bash
   git diff --cached
   ```
4. **Generate & Commit**: Generate a professional message following [Conventional Commits](https://www.conventionalcommits.org/) and execute the commit.
   ```bash
   git commit -m "<ai_generated_message>"
   ```
5. **Push**: Optionally push the changes.
   ```bash
   git push
   ```