---
name: 'step-01b-continue'
description: 'Handle workflow continuation from previous session'

outputFile: '{output_folder}/architectural-overview.md'
nextStepOptions:
  step-01-init: './step-01-init.md'
  step-02-abstraction: './step-02-abstraction.md'
  step-03-topography: './step-03-topography.md'
  step-04-synthesis: './step-04-synthesis.md'
  step-05-polish: './step-05-polish.md'
---

# Step 1b: Continue Workflow

## STEP GOAL:
To resume the architectural diagram workflow from where it was left off in a previous session.

## MANDATORY EXECUTION RULES (READ FIRST):
### Universal Rules:
- 🛑 NEVER generate content without user input
- 📖 CRITICAL: Read the complete step file before taking any action
- 🔄 CRITICAL: When loading next step with 'C', ensure entire file is read
- 📋 YOU ARE A FACILITATOR, not a content generator
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

## CONTEXT BOUNDARIES:
- User has run this workflow before.
- `{outputFile}` exists with the `stepsCompleted` array in the frontmatter.
- We need to precisely route to the correct next step.

## MANDATORY SEQUENCE

**CRITICAL:** Follow this sequence exactly. Do not skip, reorder, or improvise unless user explicitly requests a change.

### 1. Welcome Back
Say: "**Welcome back to the Architectural Diagram Creator!** Let me check the output document to see where we left off..."

### 2. Read stepsCompleted from Output
- Locate and load `{outputFile}`.
- Read the frontmatter `stepsCompleted` array directly.

### 3. Determine Next Step
- Look at the *last* item in the `stepsCompleted` array.
- Determine which phase-gate or step follows logically based on the `nextStepOptions` map in this file's frontmatter.
- (E.g., if the last step was `step-02-abstraction.md`, you load `step-03-topography.md`).

### 4. Present MENU OPTIONS
Display: **Ready to Resume. Select an Option:** [C] Continue to [Name of Next Step]

#### EXECUTION RULES:
- ALWAYS halt and wait for user input after presenting menu
- ONLY proceed to next step when user selects 'C'

#### Menu Handling Logic:
- IF C: Load the appropriate next step file exactly as determined, read the entire file, then execute immediately.
- IF Any other: help user, then redisplay menu.

## 🚨 SYSTEM SUCCESS/FAILURE METRICS:
### ✅ SUCCESS:
Correctly routing back into the workflow sequence without loss of prior abstraction context. 

### ❌ SYSTEM FAILURE:
Failing to read `{outputFile}` frontmatter, or loading an incorrect or nonexistent step step.

**Master Rule:** Skipping steps is FORBIDDEN.
