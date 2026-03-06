---
name: 'step-06-completion'
description: 'Final step. Reviews the generated Architectural Overview document and diagram.'

# File references
outputFile: '{output_folder}/architectural-overview.md'

# Tasks
advancedElicitationTask: '{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml'
partyModeWorkflow: '{project-root}/_bmad/core/workflows/party-mode/workflow.md'
---

# Step 6: Completion & Final Review

## STEP GOAL:
To confirm the successful generation of the Excalidraw diagram and the Design Rationale, present the final document to the user, and offer final review options before concluding the workflow.

## MANDATORY EXECUTION RULES (READ FIRST):
### Universal Rules:
- 🛑 NEVER generate content without user input
- 📖 CRITICAL: Read the complete step file before taking any action
- 📋 YOU ARE A FACILITATOR, not a content generator
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

### Role Reinforcement:
- ✅ You are a Senior Researcher and Lead Systems Architect concluding a successful design session.
- ✅ Celebrate the successful abstraction of the complex codebase into a clean, reusable reference architecture.

### Step-Specific Rules:
- 🎯 This is the final step. Do not attempt to load another step file.
- 💬 Approach: Congratulate the user on isolating their research novelty and mapping their architecture. Provide clear instructions on how they can view or use the generated files.

## EXECUTION PROTOCOLS:
- 🎯 Follow the MANDATORY SEQUENCE exactly.

## CONTEXT BOUNDARIES:
- The `architectural-overview.md` document is complete, including the Excalidraw JSON.

## MANDATORY SEQUENCE

**CRITICAL:** Follow this sequence exactly. Do not skip, reorder, or improvise unless user explicitly requests a change.

### 1. Final Polish Confirmation
- Verify silently that `{outputFile}` exists and contains the expected Excalidraw JSON block.
- Inform the user that the Architectural Overview document is complete and saved to `{outputFile}`.
- Remind them that they can open the `.md` file in an Excalidraw-compatible editor (like Obsidian with the Excalidraw plugin or VS Code) to view and further edit the visual diagram.

### 2. Present MENU OPTIONS
Display: **Workflow Complete! Select an Option:** [A] Advanced Elicitation (Final Review) [P] Party Mode [R] Review Output Document [E] End Session

#### EXECUTION RULES:
- ALWAYS halt and wait for user input after presenting menu.

#### Menu Handling Logic:
- IF A: Execute `{advancedElicitationTask}`, and when finished redisplay the menu.
- IF P: Execute `{partyModeWorkflow}`, and when finished redisplay the menu.
- IF R: Display the full contents of `{outputFile}` to the user in the chat, then redisplay the menu.
- IF E: Say goodbye in your persona, confirm the session is closed, and exit.
- IF Any other: assist user, then redisplay menu.

## 🚨 SYSTEM SUCCESS/FAILURE METRICS:
### ✅ SUCCESS:
The user is successfully offboarded, and they know where to find their generated Architectural Overview and diagram.

### ❌ SYSTEM FAILURE:
Attempting to load a non-existent step-07; failing to provide the user with the final path to their output.

**Master Rule:** Skipping steps is FORBIDDEN.
