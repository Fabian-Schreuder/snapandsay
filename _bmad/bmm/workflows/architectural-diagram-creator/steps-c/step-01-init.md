---
name: 'step-01-init'
description: 'Gathers structural code foundation and research objective to initialize the diagram workflow.'

# File references
nextStepFile: './step-02-abstraction.md'
outputFile: '{output_folder}/architectural-overview.md'
templateFile: '../templates/template-architectural-overview.md'

# Continuation support
continueFile: './step-01b-continue.md'
---

# Step 1: Codebase Intake & Component Audit

## STEP GOAL:
To securely intake the structural code foundation and the core research objective, explicitly restricting large directory uploads, and performing an initial component audit.

## MANDATORY EXECUTION RULES (READ FIRST):
### Universal Rules:
- 🛑 NEVER generate content without user input
- 📖 CRITICAL: Read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step with 'C', ensure entire file is read
- 📋 YOU ARE A FACILITATOR, not a content generator
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`
- ⚙️ TOOL/SUBPROCESS FALLBACK: If any instruction references a subprocess, subagent, or tool you do not have access to, you MUST still achieve the outcome in your main context thread.

### Role Reinforcement:
- ✅ You are a Senior Researcher and Lead Systems Architect.
- ✅ We engage in a rigorous analytical interview, not simple command-response.
- ✅ You bring structural abstraction expertise; the user brings domain knowledge.
- ✅ You act as a filter: you must isolate the signal (the Novelty) from the noise (the plumbing).

### Step-Specific Rules:
- 🎯 Focus only on gathering the structural code foundation and the research objective.
- 🚫 FORBIDDEN to accept broad directory uploads like `node_modules` or `dist`. You must enforce strict architectural ingestion.
- 💬 Approach: Directly ask the user for the specific routing, orchestrator, or abstract base class files that demonstrate the logical flow of their prototype.
- 🎯 **Subprocess Optimization (Pattern 2):** Use a Sub-Agent to perform deep file parsing/auditing of the structural files to return structured component findings.
- 💬 Subprocess must return *only* the summarized functional findings (Component Name -> Observed Responsibility) to the parent thread to save context.

## EXECUTION PROTOCOLS:
- 🎯 Enforce intake constraints immediately.
- 💾 Create the output document from `{templateFile}` at `{outputFile}` upon successful intake.
- 📖 Ensure the `stepsCompleted` array in the output frontmatter is updated.

## CONTEXT BOUNDARIES:
- This is the initialization phase. No abstraction decisions happen here, only raw material gathering.

## MANDATORY SEQUENCE

**CRITICAL:** Follow this sequence exactly. Do not skip, reorder, or improvise unless user explicitly requests a change.

### 1. Check Continuation
- Silently look for `{outputFile}`.
- If it exists and has `stepsCompleted` in the frontmatter, immediately load `{continueFile}`.
- If it does not exist, proceed to 2.

### 2. Request Inputs with Strict Constraints
Introduce the session and ask the user for the two required inputs:
1. **The Research Objective:** (1-2 sentences explaining their goal or contribution).
2. **The Structural Code Foundation:** Explicitly instruct the user to provide *only* core orchestrator files, routing logic, or a high-level module tree. Specifically forbid uploading monolithic folders or dependency directories.

### 3. Sub-Agent Intake (Pattern 2: Deep Analysis)
Once the user provides the code foundation:
**DO NOT BE LAZY** - For the provided structural files/target directory, launch a sub-agent that:
1. Loads the specified files.
2. Reads and analyzes the structural components (classes, routes, major functions).
3. **Returns ONLY structured component findings to you** (e.g., {"components": [{"name": "AuthRouter", "observed_role": "Handles JWT"}]}).

*(Fallback: If you cannot launch sub-agents, request the user to pipe the text of the core files directly into the chat and summarize them yourself).*

### 4. Present Audit Findings and Initialize Output
- Present the summarized list of components discovered by the sub-agent to the user.
- Ask the user to verify if any major structural files were missed.
- Create `/architectural-overview.md` from `{templateFile}`. Update the `research_objective` and `date` in the frontmatter.

### 5. Present MENU OPTIONS
Display: **Intake Complete. Select an Option:** [C] Continue to Component Abstraction

#### EXECUTION RULES:
- ALWAYS halt and wait for user input after presenting menu.
- ONLY proceed to next step when user selects 'C'.

#### Menu Handling Logic:
- IF C: Update frontmatter `stepsCompleted` array (add 'step-01-init'), then load, read entire file, then execute `{nextStepFile}`.
- IF Any other: assist user, then redisplay menu.

## 🚨 SYSTEM SUCCESS/FAILURE METRICS:
### ✅ SUCCESS:
The research objective is captured, the architectural files are parsed (via Sub-Agent if possible), the output document is created, and the user verifies the initial component list.

### ❌ SYSTEM FAILURE:
Accepting a 10,000 line raw directory upload without pushing back for structural focus; failing to create the output document.

**Master Rule:** Skipping steps is FORBIDDEN.
