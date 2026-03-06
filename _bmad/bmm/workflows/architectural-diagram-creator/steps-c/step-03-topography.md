---
name: 'step-03-topography'
description: 'Visual layout planning to generate Mermaid syntax and secure user approval on structural flow.'

# File references
nextStepFile: './step-04-synthesis.md'
outputFile: '{output_folder}/architectural-overview.md'

# Tasks
advancedElicitationTask: '{project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml'
partyModeWorkflow: '{project-root}/_bmad/core/workflows/party-mode/workflow.md'
---

# Step 3: Visual Topography & Diagram Planning

## STEP GOAL:
To structure the approved functional abstractions into a visual hierarchy, generating accurate Mermaid syntax, and securing the user's approval on the visual flow prior to synthesizing the architectural rationale.

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
- ✅ You translate abstract concepts into spatial topographies.

### Step-Specific Rules:
- 🎯 Focus entirely on the *spatial relationship* of the abstracted components defined in Step 2.
- 🚫 FORBIDDEN to proceed without the user approving the generated Mermaid diagram flow.
- 💬 Approach: Propose a logical grouping (e.g., Client, Gateway, Processing, Persistence) and flow direction (e.g., Left-to-Right).
- 🧩 **LLM Constraint:** Generate robust `mermaid` syntax to represent the architecture. Do not attempt raw Excalidraw JSON math here; the Mermaid code will be converted in Step 5.

## EXECUTION PROTOCOLS:
- 🎯 Follow the MANDATORY SEQUENCE exactly.
- 💾 Write the approved Mermaid syntax directly to the `outputFile` as a temporary placeholder block for Step 5 to consume.
- 📖 Ensure frontmatter `stepsCompleted` is updated before loading the next step.

## CONTEXT BOUNDARIES:
- Available: The `2. Component Abstraction Mapping` table from `{outputFile}`.
- Limits: Use only the approved generic terminology (e.g., "Persistence Layer"), do not regress to vendor names (e.g., "Supabase").
- Dependencies: The Novelty Kernel and Abstraction Mapping must already exist in `{outputFile}`.

## MANDATORY SEQUENCE

**CRITICAL:** Follow this sequence exactly. Do not skip, reorder, or improvise unless user explicitly requests a change.

### 1. Propose Topography
- Load `{outputFile}` and review the Component Abstraction Mapping.
- Propose a visual topography to the user:
  - What are the major boundaries/groups? (e.g., Application Layer, Core Engine, Data Layer)
  - What is the primary data or logical flow? (e.g., User -> API -> ML Pipeline -> Database)
  - Where should the "Novelty Kernel" be positioned to ensure it is the focal point of the diagram?

### 2. Generate Mermaid Draft
- Based on the proposed topography, generate a strict and robust `mermaid` block.
- Render the `mermaid` block in the chat for the user to review conceptually.

### 3. Iterate Visual Flow
- Ask the user to review the generated diagram logic.
  - Are the arrows pointing the right way?
  - Has the Novelty been adequately highlighted?
- Refine the `mermaid` syntax based on their feedback.

### 4. Format and Persist 
Once the user approves the Mermaid visual flow:
- Inject the final Mermaid syntax block underneath the `<!-- EXCALIDRAW_JSON_START -->` placeholder in `{outputFile}`. Note: You are placing the Mermaid syntax here temporarily so Step 05 can read it and execute the `excalidraw-diagram-skill`.

### 5. Present MENU OPTIONS
Display: **Topography Approved. Select an Option:** [A] Advanced Elicitation [P] Party Mode [C] Continue to Rationale Synthesis

#### EXECUTION RULES:
- ALWAYS halt and wait for user input after presenting menu.
- ONLY proceed to next step when user selects 'C'.

#### Menu Handling Logic:
- IF A: Execute `{advancedElicitationTask}`, and when finished redisplay the menu.
- IF P: Execute `{partyModeWorkflow}`, and when finished redisplay the menu.
- IF C: Update frontmatter `stepsCompleted` array (add 'step-03-topography'), then load, read entire file, then execute `{nextStepFile}`.
- IF Any other: assist user, then redisplay menu.

## 🚨 SYSTEM SUCCESS/FAILURE METRICS:
### ✅ SUCCESS:
The abstracted components are spatially mapped, a validated Mermaid diagram is generated and approved by the user, and the syntax is temporarily committed to `{outputFile}`.

### ❌ SYSTEM FAILURE:
Attempting to output raw Excalidraw JSON coordinates directly; using vendor-specific terms that were abstracted away in Step 2; failing to emphasize the Novelty Kernel in the layout.

**Master Rule:** Skipping steps is FORBIDDEN.
