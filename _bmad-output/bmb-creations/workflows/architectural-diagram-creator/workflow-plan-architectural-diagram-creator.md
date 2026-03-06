---
stepsCompleted: ['step-01-discovery', 'step-02-classification', 'step-03-requirements', 'step-04-tools', 'step-05-plan-review']
created: 2026-03-03
status: 'VALIDATION_COMPLETE'
confirmationDate: '2026-03-03'
confirmationType: 'auto-validation'
coverageStatus: '100% matched'
validationDate: '2026-03-03'
validationReport: './validation-report-2026-03-03.md'
---

# Workflow Creation Plan

## Discovery Notes

**User's Vision:**
The user wants to create a workflow that helps researchers and architects abstract complex codebases into generalized Reference Architectures using Excalidraw diagrams. The goal is to contribute to "design knowledge" by focusing on the logical flow, decision gates, and novel mechanisms ("secret sauce"), allowing the logic to be replicated using different tools or technologies.

**Who It's For:**
Researchers and Lead Architects who need to write papers or technical whitepapers contributing design knowledge to the community.

**What It Produces:**
A clean, abstracted Excalidraw diagram that highlights functional components over technical implementation. The diagram must perfectly mirror the structure of an accompanying academic or technical narrative (e.g., "Architectural Overview" or "Design Rationale").

**Key Insights:**
- The workflow must act as an analytical filter, guiding the user on *what* to diagram before teaching them *how*.
- It should prompt users to identify the core novel mechanisms.
- It must enforce abstraction (e.g., renaming specific tools like AWS S3 or PostgreSQL to functional roles like Object Storage or Relational Database).
- It must help users trim the fat by hiding standard plumbing infrastructure.
- The workflow teaches the user how to think like an architect rather than a coder.

## Classification Decisions

**Workflow Name:** architectural-diagram-creator
**Target Path:** /home/fabian/dev/work/snapandsay/_bmad/bmm/workflows/architectural-diagram-creator/

**4 Key Decisions:**
1. **Document Output:** true
2. **Module Affiliation:** BMM
3. **Session Type:** continuable
4. **Lifecycle Support:** tri-modal

**Structure Implications:**
- Creates a persistent document capturing the architectural design rationale.
- Placed in the `bmm` module workflows directory (`_bmad/bmm/workflows/architectural-diagram-creator/`).
- Needs `step-01b-continue.md` since the abstraction process could span multiple sessions and tokens.
- Needs `steps-c/`, `steps-e/`, and `steps-v/` for full lifecycle support (Create, Edit, Validate).
- Requires a free-form output format template with variables tracked in frontmatter (`stepsCompleted`, `lastStep`, etc.)

## Requirements

**Flow Structure:**
- Pattern: Linear backbone with localized looping (Iterative Refinement) in the crucial abstraction phase.
- Phases: 
  1. Codebase Intake & Component Audit. *Constraint: AI must explicitly request ONLY structural files (e.g., orchestrator routes, abstract base classes) or high-level module trees. Forbid broad uploads like `node_modules`.*
  2. Functional Abstraction & DSR Alignment (Looping Phase). *Pushback Limit: If the user cannot explain their kernel after 2-3 attempts, the AI must offer a multiple-choice hypothesis based on the codebase rather than trapping them in an infinite loop.*
  3. Visual Topography & Diagram Planning
  4. Synthesis & Rationale Generation
- Estimated steps: 5 (including initialization)

**User Interaction:**
- Style: Guided Session (AI acts as a Senior Researcher/Architect conducting an interview)
- Decision points:
  1. The "Novelty" Decision (selecting the core research contribution vs. plumbing)
  2. The Abstraction Approval (approving the text-based mapping before diagramming)
  3. The "Why" Justification (answering targeted questions to draft the rationale)
- Checkpoint frequency: Frequent (every phase-gate)

**Inputs Required:**
- Required: Structural Code Foundation. *Must be strictly limited to core orchestrator files (e.g., main.py, routing logic) or a high-level module tree.* Research Objective (1-2 sentences). 
- Optional: Previous "Ugly" Diagrams (whiteboard sketches), Mathematical/Logical Kernels
- Prerequisites: A Functional Prototype (finalized conceptual model), Domain Context (target audience, e.g., SE journal vs. informatics)

**Output Specifications:**
- Type: Document (Architectural Overview/Design Rationale with Excalidraw diagram embedded/linked).
- Format: Semi-structured (Core sections + optional additions).
- Sections: Core Mechanism/Novelty, Component Abstraction Mapping, Architectural Rationale, Excalidraw Source/Diagram.
- Frequency: Continuous refinement over the session.
- **Kernel Formatting Rule:** The core research contribution (the mathematical/logical "kernel" or "secret sauce") must be explicitly captured, formatted prominently (e.g., LaTeX block), and centralized in both the text output and the resulting visual diagram.

**Success Criteria:**
- The resulting document must clearly separate the structural codebase reality into abstract functional components.
- The user must successfully pass all 3 phase-gates (Novelty, Abstraction, Justification).
- The final artifact must contain a cohesive Design Rationale that explains the "why".

**Instruction Style:**
- Overall: Mixed (Intent-based for the discovery/why discussions; Prescriptive for the phase-gates to ensure compliance and structure).

## Tools Configuration

**Core BMAD Tools:**
- **Advanced Elicitation:** included - Integration point: Phase 2 and Phase 4, specifically for the "Why" Justification phase-gate to pressure-test the architectural rationale.
- **Party Mode:** excluded
- **Brainstorming:** excluded

**LLM Features:**
- **Web-Browsing:** excluded
- **File I/O:** included - Operations: Read the Structural Code Foundation files/directory structure.
- **Sub-Agents:** included - Use case: Phase 1 (Codebase Intake) to traverse the directory structure and perform preliminary audits while the main workflow engages the user.
- **Sub-Processes:** excluded

**Memory:**
- Type: continuable
- Tracking: `stepsCompleted`, `lastStep` in the free-form output frontmatter.

**External Integrations:**
- **excalidraw-diagram-skill:** included - Purposes: To generate the abstracted Excalidraw representation. *Refinement: Large LLMs struggle with raw Excalidraw coordinate math. The core workflow should focus on generating robust Mermaid syntax, which is then handed off to the `excalidraw-diagram-skill` to safely render and convert into the final Excalidraw canvas.*

**Installation Requirements:**
- None beyond ensuring the `excalidraw-diagram-skill` is available in the environment.

---

## Step Structure Design

### 1. Step Structure & Sequence
A 6-file micro-architecture to support the 4 phases and continuation:

- **`step-01-init.md` (Continuable Init):** Gathers Required Inputs (Structural Code Foundation, Research Objective). Validates constraints (explicitly rejecting broad uploads like `node_modules`). Creates the initial output document from a template.
- **`step-01b-continue.md` (Continuation Handler):** Checks `stepsCompleted` to seamlessly resume users who drop off between phases.
- **`step-02-abstraction.md` (Middle Standard):** Phase 2 logic. Component abstraction and the **Novelty Decision Phase-Gate**. *Pushback Limit: If 3 failed attempts to explain the kernel, present a multiple-choice hypothesis.* Concludes with the **Abstraction Approval Phase-Gate** (user approves text-based mapping before proceeding to visuals).
- **`step-03-topography.md` (Middle Standard):** Phase 3 logic. Focuses entirely on spatial relationships. Plans visual hierarchy, generates **Mermaid syntax**, and secures the user's approval on the visual flow.
- **`step-04-synthesis.md` (Middle Standard):** Phase 4 logic. Rationale generation and the **"Why" Justification Phase-Gate** (easier post-visual). Synthesizes the Design Rationale document explaining the specific architectural choices.
- **`step-05-polish.md` (Final Polish):** Passes the approved Mermaid syntax to the `excalidraw-diagram-skill` to convert to Excalidraw JSON. Formats the Kernel explicitly (e.g., LaTeX block) and performs final document coherence checks before injecting the JSON into the designated template landing zone.

### 2. Interaction Patterns
- **Guided Dialogue:** All middle steps use a conversational "interview" approach.
- **Menu Options:** 
  - Standard `[C] Continue` menus for moving between phases.
  - Phase 4 explicitly includes `[A] Advanced Elicitation` menu option to heavily pressure-test the architectural rationale.

### 3. Subprocess Optimization (File I/O & Intake)
- **Phase 1 Subprocess (Pattern 2):** Launch a sub-agent to read the specific structural files (or directory tree), perform the component audit independently, and return *only the summarized functional findings* to the main thread.
- **Graceful Fallback:** If sub-agent capability is unavailable, explicitly request the user pipe the files directly in the chat.

### 4. File Structure Design
- `steps-c/*.md` (The step files listed above)
- `templates/template-architectural-overview.md` (Output document shell containing predefined sections for the Kernel, Abstraction Mapping, Rationale, and specific demarcated landing zones like `<!-- EXCALIDRAW_JSON_START -->` for the explicit diagram injection).

---

## Foundation Build Complete

**Created:**
- Folder structure at: `/home/fabian/dev/work/snapandsay/_bmad/bmm/workflows/architectural-diagram-creator/`
- `workflow.md`
- Main template: `template-architectural-overview.md`

**Configuration:**
- Workflow name: `architectural-diagram-creator`
- Continuable: yes
- Document output: yes - semi-structured document
- Mode: tri-modal (Create/Edit/Validate)

**Next Steps:**
- Step 8: Build `step-01-init.md` (and `step-01b-continue.md` since it is continuable)
- Step 9: Build remaining progression steps

---

## Step 01 Build Complete

**Created:**
- `steps-c/step-01-init.md`
- `steps-c/step-01b-continue.md`

**Step Configuration:**
- Type: Continuable
- Input Discovery: No
- Next Step: `step-02-abstraction.md`

**Supporting Files:**
- `templates/template-architectural-overview.md` (Created in Foundation Build)

---

## Step 02 Build Complete

**Created:**
- `steps-c/step-02-abstraction.md`

**Step Configuration:**
- Type: Middle Step (Standard)
- Outputs to: `architectural-overview.md` (Sections 1 & 2)
- Next Step: `step-03-topography.md`

**Supporting Files:**
- None (Uses core template and advanced elicitation tasks)

---

## Step 03 Build Complete

**Created:**
- `steps-c/step-03-topography.md`

**Step Configuration:**
- Type: Middle Step (Standard)
- Outputs to: `architectural-overview.md` (Temporary Mermaid Block injection for Step 5 processing)
- Next Step: `step-04-synthesis.md`

**Supporting Files:**
- None (Uses existing `template-architectural-overview.md`)

---

## Step 04 Build Complete

**Created:**
- `steps-c/step-04-synthesis.md`

**Step Configuration:**
- Type: Middle Step (Standard)
- Outputs to: `architectural-overview.md` (Section 4)
- Next Step: `step-05-polish.md`

**Supporting Files:**
- None (Uses advanced elicitation task)

---

## Step 05 Build Complete

**Created:**
- `steps-c/step-05-polish.md`

**Step Configuration:**
- Type: Final Polish Step (Standard)
- Outputs to: `architectural-overview.md` (Section 3)
- Next Step: `step-06-completion.md`

**Supporting Files:**
- Excalidraw Diagram Skill loaded.

---

## Step 06 Build Complete

**Created:**
- `steps-c/step-06-completion.md`

**Step Configuration:**
- Type: Final Step (Standard)
- Outputs to: None (Review Only)
- Next Step: None (Completion)

**Supporting Files:**
- None (Uses advanced elicitation task)
