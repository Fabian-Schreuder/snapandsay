# Reference Architecture for Design Science Research

This reference architecture is an abstract, academic-oriented blueprint of the Snap and Say dietary logging system. It focuses on the functional layers and data flow rather than specific implementations, mapping to the key components of the dynamic complexity scoring and routing mechanism.

```mermaid
flowchart TB
    %% Styling Definitions
    classDef userLayer fill:#E1F5FE,stroke:#0288D1,stroke-width:2px,color:#000
    classDef interfaceLayer fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#000
    classDef orchestrationLayer fill:#E8F5E9,stroke:#388E3C,stroke-width:2px,color:#000
    classDef reasoningLayer fill:#FFF3E0,stroke:#F57C00,stroke-width:2px,color:#000
    classDef persistenceLayer fill:#ECEFF1,stroke:#607D8B,stroke-width:2px,color:#000
    classDef externalLayer fill:#FFFDE7,stroke:#FBC02D,stroke-width:2px,color:#000

    %% 1. User/Client Layer
    subgraph Client ["Client Layer"]
        User([User])
        MobileApp[Mobile / Web Application]
    end

    %% 2. Interface / Gateway Layer
    subgraph Interface ["Interface & Gateway Layer"]
        API[API Gateway]
        Auth[Authentication Service]
    end

    %% 3. Orchestration & Routing Layer
    subgraph Orchestration ["Orchestration & Control Layer"]
        Router{Router / Dispatcher}
        StateMgr[State Manager]
        ComplexityScorer[Complexity Scorer]
        Workflow[Workflow Engine]
    end

    %% 4. Reasoning / Inference Layer
    subgraph Reasoning ["Inference Engine (LLM)"]
        Analyzer[Nutrition Analyzer]
        Clarifier[Clarification Generator]
    end

    %% 5. Persistence Layer
    subgraph Persistence ["Persistence Layer"]
        DB[(Relational Database)]
        BlobStore[(Object Storage)]
    end

    %% 6. External/Infrastructure Services
    subgraph ExtServices ["External Infrastructure"]
        Transcriber[Speech-to-Text Service]
    end

    %% --- Connections & Data Flow ---
    
    %% Client to Interface
    User -- "Audio/Image/Text" --> MobileApp
    MobileApp -- "Payload (Upload/Clarify)" --> API
    MobileApp -- "Stream Connection" --> API
    
    %% Interface handling
    API -- "Validate Token" --> Auth
    Auth -. "Valid" .-> API
    
    %% Interface to Orchestration
    API -- "Raw Request (Media URIs, Text)" --> StateMgr
    
    %% Uploading Media directly mapped for clarity:
    API -- "Media Files" --> BlobStore
    
    %% Orchestration Flow (The Agent Graph)
    StateMgr -- "Initial Context" --> Workflow
    Workflow -- "Transcribe needed" --> Transcriber
    Transcriber -- "Text Transcript" --> Workflow
    
    %% Main Analysis Loop
    Workflow -- "Analyze Input Context" --> Analyzer
    Analyzer -- "Initial Nutrient Est. & Confidence" --> Workflow
    
    %% Routing Logic
    Workflow -- "Evaluate Confidence" --> ComplexityScorer
    ComplexityScorer -- "Score & Metrics" --> Router
    
    %% The dynamic routing fork
    Router -- "High Confidence(≥0.85)" --> FastPath[Log Finalization]
    Router -- "Low Confidence(<0.85)" --> SlowPath[AMPM Clarification Cycle]
    
    %% Clarification branch
    SlowPath -- "Determine Missing Variables" --> Clarifier
    Clarifier -- "Q&A Formulation" --> API
    API -- "Clarification Request" --> MobileApp
    User -- "Clarification Response" --> MobileApp
    
    %% Finalization
    FastPath -- "Complete Nutrition Profile" --> StateMgr
    SlowPath -- "Refined Context" --> Workflow
    
    %% Final Persistence
    StateMgr -- "Status Update & Log Entry" --> DB

    %% Apply Classes
    class User,MobileApp userLayer;
    class API,Auth interfaceLayer;
    class Router,StateMgr,ComplexityScorer,Workflow,FastPath,SlowPath orchestrationLayer;
    class Analyzer,Clarifier reasoningLayer;
    class DB,BlobStore persistenceLayer;
    class Transcriber externalLayer;

```

## Layer Descriptions (Academic Abstraction)

1.  **Client Layer:** The primary touchpoint for the end-user, handling multimodal inputs (voice, text, image) and displaying real-time streaming feedback and clarification prompts.
2.  **Interface & Gateway Layer:** Manages authentication, session validation, and exposes defining entry points (e.g., RESTful endpoints or Server-Sent Events for streaming).
3.  **Orchestration & Control Layer:** The core state machine and workflow engine. This layer abstracts the stateful agent graph (`langgraph`), including the critical **Complexity Scorer** and **Router**. It evaluates the output of the inference engine against predefined heuristics (e.g., confidence thresholds) to dynamically route the request for immediate logging or multi-turn clarification.
4.  **Inference Engine (Reasoning Layer):** Encapsulates the Large Language Model interactions. It performs the non-deterministic semantic analysis, extracting nutritional entities from the inputs, and generates context-aware clarification questions when triggered by the orchestrator.
5.  **Persistence Layer:** Represents the durable storage of system state, user activity logs (Relational DB), and the raw multimodal artifacts (Object Storage).
6.  **External Infrastructure:** Specialized microservices or third-party APIs relied upon for isolated, specific tasks, such as Speech-to-Text transcription.
