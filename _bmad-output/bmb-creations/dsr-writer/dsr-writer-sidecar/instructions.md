# Instructions

## Output File Management

- **ALL** generated `.md` and `.tex` output files MUST be saved to `{project-root}/docs/thesis/msc-thesis-phase2/drafts/`
- Never save output files to the sidecar folder — sidecar is for memory and instructions only
- Use descriptive filenames that reflect the DSR phase or section, e.g. `problem-identification.md`, `design-and-development.tex`

## Memory Update Protocol

After completing **any** task (drafting, conversion, extraction, review, classification):

1. Open `{project-root}/_bmad/_memory/dsr-writer-sidecar/memories.md`
2. Append a dated entry with:
   - **What was produced** (file name and path)
   - **DSR phase/section** addressed
   - **User preferences** noted during the session (tone, structure, emphasis)
   - **Current thesis progress** (which sections are drafted, which remain)
3. Save the updated `memories.md`

## File Access Boundaries

- **Read/write allowed:** `{project-root}/_bmad/_memory/dsr-writer-sidecar/` AND `{project-root}/docs/thesis/msc-thesis-phase2/drafts/`
- **Read-only reference:** `{project-root}/docs/thesis/msc-thesis-phase2/references.bib` and existing drafts in `{project-root}/docs/thesis/msc-thesis-phase2/`
- **Read-only codebase:** Any source files needed for artifact extraction

## Session Greeting

On activation, always:
1. Load and review `memories.md` for prior session context
2. Provide a brief status summary of thesis drafting progress
3. Present the command menu
