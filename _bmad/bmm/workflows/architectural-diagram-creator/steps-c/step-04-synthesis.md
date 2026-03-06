---
name: 'step-04-synthesis'
description: 'Rationale generation and the "Why" Justification Phase-Gate.'

# File references
nextStepFile: './step-05-polish.md'
outputFile: '{output_folder}/architectural-overview.md'

# Tasks
advancedElicitationTask: '{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml'
partyModeWorkflow: '{project-root}/_bmad/core/workflows/party-mode/workflow.md'
---

# Step 4: Synthesis & Rationale Generation

## STEP GOAL:
To establish the architectural design rationale by querying the user on the "Why" behind their mapped architectural choices and recording this justification formally in the output document.

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
- ✅ You press for deep, reasoned justifications behind architectural decisions rather than accepting surface-level answers.

### Step-Specific Rules:
- 🎯 Focus only on extracting the "Why" behind the layout approved in Step 3.
- 🚫 FORBIDDEN to invent rationales on behalf of the user. You must elicit the context from them.
- 💬 Approach: Review the Mermaid block from Step 3. Identify 2 or 3 critical intersections or structural choices (e.g., "Why was a separate indexing layer needed before the persistence engine?"). Use targeted questioning to force the user to defend the architecture.

## EXECUTION PROTOCOLS:
- 🎯 Follow the MANDATORY SEQUENCE exactly.
- 💾 Write the established design rationale to the `4. Architectural Rationale` section of `{outputFile}`.
- 📖 Ensure frontmatter `stepsCompleted` is updated before loading the next step.

## CONTEXT BOUNDARIES:
- Available: The `<!-- EXCALIDRAW_JSON_START -->` block (currently holding Mermaid code) and the component mappings from `{outputFile}`.
- Dependencies: The visual layout must be established (Step 3 complete) so the LLM and User have a concrete map to justify.

## MANDATORY SEQUENCE

**CRITICAL:** Follow this sequence exactly. Do not skip, reorder, or improvise unless user explicitly requests a change.

### 1. Identify Key Architectural Decisions
- Silently review the generated Mermaid block and the Component Abstraction list in `{outputFile}`.
- Identify 2-3 significant design choices. Examples:
  - Bottlenecks resolved by a specific routing algorithm.
  - The isolation of the Novelty Kernel from the rest of the application state.
  - Distinct separation of concerns between specific layers.

### 2. Phase-Gate 3: The "Why" Justification
- Present the 2-3 identified design choices to the user as interview questions. 
- Ask them to explain the context, the justification (why it was chosen over alternatives), and the impact on the "Novelty" for each point.
- *Pushback Limit Enforced:* If their answer is shallow (e.g., "Because Next.js is easy"), press them for the functional or temporal reasoning behind the structural separation.

### 3. Draft the Rationale
- Based on the user's answers, draft the formal `Architectural Rationale` text.
- Follow the formatting structure in the output document: Decision Title, Context, Justification, Impact on Novelty.
- Show the draft to the user for approval.

### 4. Format and Persist 
Once the user approves the formal rationale:
- Inject the rationale text into the `4. Architectural Rationale` section of `{outputFile}`.

### 5. Present MENU OPTIONS
Display: **Rationale Approved. Select an Option:** [A] Advanced Elicitation (Highly Recommended) [P] Party Mode [C] Continue to Final Polish

#### EXECUTION RULES:
- ALWAYS halt and wait for user input after presenting menu.
- ONLY proceed to next step when user selects 'C'.

#### Menu Handling Logic:
- IF A: Execute `{advancedElicitationTask}`, and when finished redisplay the menu. *(Note: This is heavily encouraged here to pressure-test the written justification against external critique).*
- IF P: Execute `{partyModeWorkflow}`, and when finished redisplay the menu.
- IF C: Update frontmatter `stepsCompleted` array (add 'step-04-synthesis'), then load, read entire file, then execute `{nextStepFile}`.
- IF Any other: assist user, then redisplay menu.

## 🚨 SYSTEM SUCCESS/FAILURE METRICS:
### ✅ SUCCESS:
The user explicitly defends 2-3 key structural decisions, the rationale is documented formally in `{outputFile}`, and the phase-gate is passed.

### ❌ SYSTEM FAILURE:
Allowing the user to bypass the "Why" questioning; writing the rationale for the user without their explicit input; skipping the documentation step.

**Master Rule:** Skipping steps is FORBIDDEN.
