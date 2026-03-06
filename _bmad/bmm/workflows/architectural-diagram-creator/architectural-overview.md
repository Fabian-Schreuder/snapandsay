---
research_objective: 'To design and evaluate "Snap and Say," a multimodal Agentic AI system aimed at assessing longitudinal dietary intake in older adults with high clinical accuracy, while keeping the physical and cognitive workload acceptable.
'
date: '2026-03-03'
stepsCompleted:
  - step-01-init
---

# Architectural Overview: Reference Architecture Abstraction

## 1. Core Research Objective
*This section defines the "Why" and the specific novelty being introduced.*
To design and evaluate "Snap and Say," a multimodal Agentic AI system aimed at assessing longitudinal dietary intake in older adults with high clinical accuracy, while keeping the physical and cognitive workload acceptable.

### 1.1 The Kernel (Core Novelty)
The primary architectural novelty is the **Deterministic Complexity Scoring Engine**. Instead of relying entirely on LLM "black-box" confidence scores (which are unreliable for medical fidelity), the system mathematically anchors the LLM's output to a standardized clinical risk profile.
- **Mechanism (The Kernel Formula):** `C = Σ(w · L²) + P`. It calculates a deterministic complexity score based on weighted ambiguity dimensions (`hidden_ingredients`, `invisible_prep`, `portion_ambiguity`) and adds a `semantic_penalty`.
- **Purpose:** Decouples the definition of "acceptable clinical uncertainty" from the LLM, ensuring that routing into clarification loops (AMPM) is driven by a reproducible, mathematically grounded engine.


---

## 2. Component Abstraction Matrix
*This section maps system-specific components to generalized, vendor-agnostic roles.*

| Specific Component (Codebase) | Generalized Role (Reference Architecture) | Primary Responsibility |
| :--- | :--- | :--- |
| `FastAPI App (main.py)` | API Gateway / Orchestrator | Handles incoming multimodal requests (image/audio) and routing. |
| `Agent Graph (graph.py)` | State Machine / Directed Acyclic Graph (DAG) Executer | Orchestrates the sequence of analysis, gatekeeping, and clarification steps. |
| `Complexity Calculator (complexity_calculator.py)` | Deterministic Complexity Scoring Engine | Calculates mathematical risk and ambiguity scores (`C = Σ(w · L²) + P`). |
| `Routing (routing.py)` | Dynamic Policy Routing Engine | Decides graph transitions based on confidence vs. dynamic clinical thresholds. |
| `Semantic Gatekeeper` | Input Validation / Pre-processing Gate | Intercepts lexically unbounded items before deep analysis. |
| `AMPM Subgraph` | Detail Acquisition Engine / Clarification Loop | Manages the multi-pass detail cycle for logically complex or low-confidence items. |


---

## 3. Structural Topography & Interactions
*This section defines the visual flow and spatial relationship of the abstractions.*

<!-- EXCALIDRAW_JSON_START -->
```mermaid
flowchart LR
    %% Data / Flow
    subgraph Client [Client Layer]
        User([User Input: Voice/Image])
    end

    subgraph Orchestration [Application Orchestration Layer]
        API[API Gateway / Orchestrator]
    end

    subgraph Cognition [Cognitive & Evaluation Engine]
        DAG[State Machine / DAG Executer]
        Gatekeeper{Input Validation \n Pre-processing Gate}
        
        %% The Novelty
        Complexity((Deterministic Complexity\nScoring Engine\n<i>C = Σw·L² + P</i>))
        
        Router{Dynamic Policy\nRouting Engine}
        AMPM[Detail Acquisition Engine\nClarification Loop]
    end

    %% Interactions
    User -->|Multimodal Payload| API
    API -->|Initialize Context| DAG
    DAG -->|Raw Data| Gatekeeper
    
    Gatekeeper -->|Unbounded Semantic Reject| AMPM
    Gatekeeper -->|Bounded Semantic Accept| Complexity
    
    Complexity -->|Calculated Complexity Score| Router
    
    Router -->|Score > Clinical (or Low Confidence)| AMPM
    Router -->|Score <= Clinical| Finalize[Finalize Diet Log]
    
    AMPM -->|Clarification Details| User
    
    %% Styling to highlight Novelty
    style Complexity fill:#f9f,stroke:#333,stroke-width:4px
```
<!-- EXCALIDRAW_JSON_END -->

## 4. Design Rationale & Constraints
*This section provides the formal justification for the structural choices made.*

### 4.1 The Strict Isolation of the Semantic Gatekeeper
* **Context:** The `Input Validation / Pre-processing Gate` sits before the `Deterministic Complexity Scoring Engine` in the processing pipeline.
* **Justification:** It enforces a "resolve *what* before *how ambiguous*" hierarchy. If the AI attempts to calculate material ambiguity (e.g., portion uncertainty) on an unbounded generic noun like "sandwich," the resulting volume-to-calorie math is mathematically compromised because the system lacks the foundational knowledge (e.g. meatball vs vegetable density).
* **Impact on Novelty:** By intercepting and bouncing these "Umbrella Terms" early via a lexical bounding check, it protects the Deterministic Complexity Scoring Engine from garbage-in/garbage-out, ensuring the `C = Σ(w · L²) + P` formula is only applied to semantically bounded food concepts.

### 4.2 Decoupling the Routing Policy from the Scoring Engine
* **Context:** The `Deterministic Complexity Scoring Engine` calculates `C` independently of the `Dynamic Policy Routing Engine`'s decision to trigger clarification.
* **Justification:** This structural isolation decouples the objective material ambiguity of the food from the subjective clinical needs of the user. The Scoring Engine determines absolute complexity. The Routing Engine evaluates that score against a dynamic, per-session clinical threshold (`τ`).
* **Impact on Novelty:** It grants the system clinical adaptability. The exact same meal (e.g., score of 8.0) might pass silently for a general wellness user (`τ` = 15.0) but correctly trigger the AMPM clarification loop for a diabetic patient (`τ` = 5.0). This maximizes medical fidelity while minimizing unnecessary procedural workload on healthy users.

---
*End of Document. Proceeding to Excalidraw generation phase.*
