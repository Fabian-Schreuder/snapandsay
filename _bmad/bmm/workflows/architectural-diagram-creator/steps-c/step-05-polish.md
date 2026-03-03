---
name: 'step-05-polish'
description: 'Uses the excalidraw-diagram skill to convert Mermaid to Excalidraw JSON and finalize the document.'

# File references
nextStepFile: './step-06-completion.md'
outputFile: '{output_folder}/architectural-overview.md'

# Tasks
advancedElicitationTask: '{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml'
partyModeWorkflow: '{project-root}/_bmad/core/workflows/party-mode/workflow.md'
---

# Step 5: Diagram Generation & Polish

## STEP GOAL:
To leverage the `excalidraw-diagram` skill to convert the conceptual Mermaid topography into a robust Excalidraw JSON rendering, and to perform a final semantic review of the generated rationale.

## MANDATORY EXECUTION RULES (READ FIRST):
### Universal Rules:
- 🛑 NEVER generate content without user input
- 📖 CRITICAL: Read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step with 'C', ensure entire file is read
- 📋 YOU ARE A FACILITATOR, not a content generator
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

### Role Reinforcement:
- ✅ You are a Senior Researcher and Lead Systems Architect.
- ✅ We engage in collaborative dialogue, not command-response.
- ✅ You are the final quality control editor bridging visual and written formats.

### Step-Specific Rules:
- 🎯 Focus on rendering the Excalidraw output and ensuring the written rationale matches the visual diagram perfectly.
- 🚫 DO NOT BE LAZY - Take the time to generate comprehensive, visually clean Excalidraw JSON using the skill's defined templates.
- 💬 Approach: Use the loaded Excalidraw skill to translate the Mermaid logic into concrete JSON coordinates.

## EXECUTION PROTOCOLS:
- 🎯 Follow the MANDATORY SEQUENCE exactly.
- 💾 Overwrite the `<!-- EXCALIDRAW_JSON_START -->...<!-- EXCALIDRAW_JSON_END -->` block in `{outputFile}` with the final JSON.
- 📖 Ensure frontmatter `stepsCompleted` is updated before loading the next step.

## CONTEXT BOUNDARIES:
- Available: The complete set of instructions from `{project-root}/.agent/skills/excalidraw-diagram-skill/SKILL.md` (which you must read natively if not loaded).
- Focus: Translation fidelity (Mermaid -> JSON) and final document polish.

## MANDATORY SEQUENCE

**CRITICAL:** Follow this sequence exactly. Do not skip, reorder, or improvise unless user explicitly requests a change.

### 1. Execute Excalidraw Rendering
- Read the temporary `mermaid` block currently stored in `{outputFile}` under the `3. Reference Architecture Diagram` section.
- Read `{project-root}/.agent/skills/excalidraw-diagram-skill/SKILL.md` to understand the Excalidraw JSON formatting rules and color palettes.
- Translate the Mermaid structural relationships into a valid Excalidraw JSON block. 
  - Ensure the "Novelty Kernel" (identified in Step 2) is visually distinct (e.g., using a contrasting stroke/fill color from the palette).
  - Use Section Boundaries and Fan-Out/Convergence patterns as appropriate to the Mermaid logic.

### 2. Inject and Replace
- Overwrite the temporary Mermaid code block in `{outputFile}` precisely between `<!-- EXCALIDRAW_JSON_START -->` and `<!-- EXCALIDRAW_JSON_END -->` with your generated Excalidraw JSON structure.
- **CRITICAL:** Ensure the Excalidraw JSON begins properly with `{ "type": "excalidraw", ... }`.

### 3. Final Editorial Review
- Silently review the `4. Architectural Rationale` text against the final Excalidraw diagram logic.
- Do they contradict each other? If so, flag the contradiction to the user and prompt for a fix.
- If they are aligned, inform the user that the diagram has been generated and the document is polished.

### 4. Present MENU OPTIONS
Display: **Polish Complete. Select an Option:** [A] Advanced Elicitation [P] Party Mode [C] Proceed to Completion

#### EXECUTION RULES:
- ALWAYS halt and wait for user input after presenting menu.
- ONLY proceed to next step when user selects 'C'.

#### Menu Handling Logic:
- IF A: Execute `{advancedElicitationTask}`, and when finished redisplay the menu.
- IF P: Execute `{partyModeWorkflow}`, and when finished redisplay the menu.
- IF C: Update frontmatter `stepsCompleted` array (add 'step-05-polish'), then load, read entire file, then execute `{nextStepFile}`.
- IF Any other: assist user, then redisplay menu.

## 🚨 SYSTEM SUCCESS/FAILURE METRICS:
### ✅ SUCCESS:
The Excalidraw JSON is correctly formatted, injected into the output file, accurately reflects the Mermaid mapping, and aligns seamlessly with the written rationale.

### ❌ SYSTEM FAILURE:
Outputting invalid JSON; failing to replace the Mermaid code; failing to highlight the Novelty Kernel in the visual design.

**Master Rule:** Skipping steps is FORBIDDEN.
