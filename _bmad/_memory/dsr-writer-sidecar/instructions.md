# Instructions

## Output File Management
- All generated `.md` draft files → `{project-root}/docs/thesis/msc-thesis-phase2/drafts/`
- All generated `.tex` files → `{project-root}/docs/thesis/msc-thesis-phase2/drafts/`
- Naming convention: `{dsrm_phase_or_topic}_draft.md` (e.g., `objectives_of_solution_draft.md`)
- LaTeX conversions keep the same base name with `.tex` extension

## Memory Update Protocol
- **After every task** (draft, review, conversion, extraction, classification): update `memories.md` with:
  - What was produced (file name, DSRM phase, word count)
  - Any user preferences noted during the session
  - Current thesis progress summary
  - Outstanding review findings or TODOs
- Memory updates are **mandatory**, not optional — they enable cross-session continuity

## File Access Boundaries
- **Read/Write**: `{project-root}/_bmad/_memory/dsr-writer-sidecar/` (sidecar memory)
- **Read/Write**: `{project-root}/docs/thesis/msc-thesis-phase2/drafts/` (output directory)
- **Read only**: `{project-root}/docs/thesis/msc-thesis-phase2/references.bib` (citations)
- **Read only**: `{project-root}/backend/` (codebase for artifact extraction)
- **Read only**: `{project-root}/_bmad-output/` (story specs, architecture docs)
- **Read only**: `{project-root}/docs/thesis/msc-thesis-phase2/chapters/` (existing LaTeX chapters)

## Session Greeting Rules
- Always scan `drafts/` directory at session start to assess current thesis progress
- Load `memories.md` to recall prior session context and user preferences
- Provide a brief status summary table in the greeting before displaying the menu

## Citation Protocol
- Always verify citation keys exist in `references.bib` before using them in drafts
- Use Pandoc-style `[@key]` notation in Markdown drafts
- Use `\cite{key}` notation in LaTeX conversions
- When a claim lacks a supporting citation, flag it explicitly rather than omitting silently
