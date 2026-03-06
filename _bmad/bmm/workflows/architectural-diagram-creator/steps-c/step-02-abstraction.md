---
name: 'step-02-abstraction'
description: 'Component abstraction and the Novelty Decision Phase-Gate.'

# File references
nextStepFile: './step-03-topography.md'
outputFile: '{output_folder}/architectural-overview.md'

# Tasks
advancedElicitationTask: '{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml'
partyModeWorkflow: '{project-root}/_bmad/core/workflows/party-mode/workflow.md'
---

# Step 2: Functional Abstraction & DSR Alignment

## STEP GOAL:
To abstract the codebase components into generic functional roles, isolate the "Novelty" (the core research contribution), and secure the user's approval on the text-based mapping before proceeding to visuals.

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
- ✅ You bring structural abstraction expertise; the user brings domain knowledge.

### Step-Specific Rules:
- 🎯 Focus only on mapping components to functional roles and isolating the Novelty.
- 🚫 FORBIDDEN to proceed without explicit user approval of the mapping (Abstraction Approval Phase-Gate).
- 💬 Approach: Use targeted questions to challenge the user's definition of novelty.
- ⚙️ **Pushback Limit:** If the user fails to explain the core mathematical/logical "kernel" (novelty) clearly after 3 attempts, you MUST offer a multiple-choice hypothesis based on the codebase to move forward. Do not trap them in an infinite loop.

## EXECUTION PROTOCOLS:
- 🎯 Follow the MANDATORY SEQUENCE exactly.
- 💾 Append the approved mapping and kernel description to `{outputFile}` upon completion of the phase-gates.
- 📖 Ensure frontmatter `stepsCompleted` is updated before loading the next step.

## CONTEXT BOUNDARIES:
- The structural files have been parsed, and the initial component list is known from Step 1.
- Focus: Functional mapping and DSR novelty isolation.
- Dependencies: The `{outputFile}` must exist with the Research Objective defined.

## MANDATORY SEQUENCE

**CRITICAL:** Follow this sequence exactly. Do not skip, reorder, or improvise unless user explicitly requests a change.

### 1. Phase-Gate 1: The "Novelty" Decision
- Review the Research Objective and the initial component list from Step 1.
- Ask the user to explicitly identify which component or specific sub-routine represents the *core research contribution* (the "Novelty" or "Secret Sauce").
- If their answer is vague or focuses on standard plumbing (e.g., "The PostgreSQL database"), push back. Remind them of the structural elements.
- *Pushback Limit Enforced:* Track attempts. After 3 unsuccessful attempts to isolate a valid architectural or logical novelty, synthesize a multiple-choice list of 2-3 likely structural novelties based on the intake, and ask them to pick one.

### 2. Isolate the Kernel
- Once the Novelty is identified, ask the user to provide the mathematical formula, specific logical threshold, algorithm, or unique mechanism that drives it. 
- You will format this as the "Kernel" in the final document.

### 3. Component Abstraction Mapping
- Present the initial list of raw components (Vendor names, specific libraries).
- Propose a 1-to-1 mapping translating these into generic functional roles (e.g., Supabase -> Persistence Layer; Next.js router -> API Gateway).
- Ask the user to review the proposed mapping. 

### 4. Phase-Gate 2: The Abstraction Approval
- The user must explicitly approve your text-based functional mapping or provide corrections.
- Iterate the mapping until the user says it accurately reflects the generalized architecture.

### 5. Document the Approved State
Once Phase-Gate 2 is passed:
- Append the "Kernel" definition to the `1. Core Mechanism & Novelty` section of `{outputFile}`.
- Append the approved mapping table to the `2. Component Abstraction Mapping` section of `{outputFile}`.

### 6. Present MENU OPTIONS
Display: **Abstraction Approved. Select an Option:** [A] Advanced Elicitation [P] Party Mode [C] Continue to Topography Planning

#### EXECUTION RULES:
- ALWAYS halt and wait for user input after presenting menu.
- ONLY proceed to next step when user selects 'C'.

#### Menu Handling Logic:
- IF A: Execute `{advancedElicitationTask}`, and when finished redisplay the menu.
- IF P: Execute `{partyModeWorkflow}`, and when finished redisplay the menu.
- IF C: Update frontmatter `stepsCompleted` array (add 'step-02-abstraction'), then load, read entire file, then execute `{nextStepFile}`.
- IF Any other: assist user, then redisplay menu.

## 🚨 SYSTEM SUCCESS/FAILURE METRICS:
### ✅ SUCCESS:
The Novelty is successfully isolated (either naturally or via the pushback mechanism), the user explicitly approves the abstracted functional mapping, and `{outputFile}` is updated.

### ❌ SYSTEM FAILURE:
Proceeding to Map visual topography without the user explicitly approving the text-based abstraction; allowing the user to iterate endlessly without triggering the multiple-choice pushback fallback.

**Master Rule:** Skipping steps is FORBIDDEN.
