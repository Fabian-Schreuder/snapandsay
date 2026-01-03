\section{Introduction}

Managing chronic conditions such as diabetes and sarcopenia in older adults requires accurate longitudinal dietary assessment \cite{shimDietaryAssessmentMethods2014,evertNutritionTherapyAdults2019}. The current gold standard, the Weighed Food Record (WFR), necessitates manually weighing and logging every ingredient \cite{shimDietaryAssessmentMethods2014,willettNutritionalEpidemiology2012}. While highly accurate, the associated cognitive and physical burden creates significant friction, leading to poor compliance outside clinical trials \cite{burkeSelfMonitoringWeightLoss2011,cordeiroBarriersNegativeNudges2015,thompsonDietaryAssessmentMethodology2017}.

Existing digital health interventions present a binary trade-off ill-suited for the geriatric demographic. Manual logging offers high fidelity but imposes high friction through complex navigation and text entry, conflicting with age-related declines in motor skills and visual acuity \cite{wildenbosAgingBarriersInfluencing2018,czajaImpactAgingAccess2007,berkowskyFactorsPredictingDecisions2017}. Conversely, passive computer vision reduces friction but suffers from low fidelity. These systems rely on single-shot inference that often fails to perceive hidden ingredients, such as added sugars or fats, or query missing context, often resorting to unreliable probabilistic assumptions \cite{minSurveyFoodComputing2019,loImageBasedFoodClassification2020}.

This limitation is substantiated by our preceding scoping review of AI in geriatric nutrition \textit{[Citation Needed]}. Analysis of 25 eligible studies revealed that 92\% of existing applications remain in prototype or pilot phases (median sample size $n=28$), often lacking operational validity. While the literature addresses visual recognition accuracy \cite{minSurveyFoodComputing2019,loImageBasedFoodClassification2020}, there is a demonstrated lack of deployed agentic AI workflows capable of self-auditing low confidence. Specifically, few systems actively intervene via conversational repair or apply suppression logic to minor ambiguities to balance data fidelity with user fatigue.

This study proposes the design and evaluation of "Snap and Say," a multimodal Agentic AI system. Utilizing a graph-based cognitive architecture \cite{chaseLangChain2022,weiChainofthoughtPromptingElicits2022,yaoReActSynergizingReasoning2022}, the system implements active reasoning to shift from static input methods to collaborative dialogue. We hypothesize this approach maintains accuracy comparable to the WFR while keeping the perceived workload acceptable for older adults.

To evaluate the system, this study investigates three core questions. First, we assess how a multi-turn agentic photo-dialogue workflow affects per-meal mean absolute error (MAE) in estimated energy and macronutrients relative to a single-shot photo-only estimator, utilizing WFR as ground truth. Second, we examine how confidence-gated clarification alters interaction friction and estimation accuracy relative to an always-clarify policy. Finally, we analyze the turn-level and end-to-end latencies of the agentic self-correction workflow to determine if they meet predefined acceptability thresholds for older adults \cite{nielsenUsabilityEngineering1994,nahStudyTolerableWaiting2004}.

\section{Methodology}

This study adopts the Design Science Research (DSR) methodology to systematically develop and evaluate the "Snap and Say" system. We utilize the DSR Process Model proposed by Peffers et al. \cite{peffersDesignScienceResearch2007}, which provides a nominal sequence of six phases. This approach ensures that the design process is driven by the practical needs of the geriatric population (*Relevance Cycle*) while being grounded in existing theories of multimodel learning and cognitive architectures (*Rigor Cycle*) \cite{hevnerDesignScienceInformation2004}.

The six phases of the research process are instantiated as follows:

\subsection{Phase 1: Problem Identification and Motivation}
As detailed in the Introduction, current dietary assessment methods force a binary trade-off between high-friction/high-accuracy manual logging (WFR) and low-friction/low-accuracy passive computer vision. This gap creates a specific barrier for older adults suffering from motor skills and visual acuity declines \cite{wildenbosAgingBarriersInfluencing2018}. The research motivation is to decouple this trade-off using agentic AI.

\subsection{Phase 2: Define the Objectives of a Solution}
The objective is to design a multimodal artifact capable of "self-auditing" low-confidence inferences. The system must meet three functional requirements derived from the problem analysis:
\begin{itemize}
    \item \textbf{FR1 (Agentic Logic):} The system must actively query the user ("Say") only when visual confidence falls below a specific threshold, avoiding unnecessary fatigue.
    \item \textbf{FR2 (Multimodality):} The interaction must support voice input to bypass text-entry barriers common in geriatric populations.
    \item \textbf{FR3 (Latency):} The active reasoning loop must operate within tolerability thresholds defined by Nah \cite{nahStudyTolerableWaiting2004} to prevent user abandonment.
\end{itemize}

\subsection{Phase 3: Design and Development}
The artifact, "Snap and Say," is designed as a graph-based agentic workflow. We draw upon the Knowledge Base of Chain-of-Thought (CoT) prompting \cite{weiChainofthoughtPromptingElicits2022} and ReAct paradigms \cite{yaoReActSynergizingReasoning2022} to restructure the dietary assessment task.

Unlike standard single-shot classifiers, we implement the system using a directed cyclic graph architecture (e.g., LangGraph). This allows the state machine to loop through a "Critique step." The agent evaluates visual features; if ambiguity regarding ingredients (e.g., added fats) is detected, the agent transitions to a "Question Generation" node rather than a final "Estimation" node. This iterative design process involved two cycles of refinement to tune the suppression logic (confidence gating).

\subsection{Phase 4: Demonstration}
To demonstrate the artifact's utility, the system is instantiated as a mobile web application accessible on standard smartphones. The demonstration utilizes a controlled "Meal Simulation Protocol," where distinct dishes with varying degrees of visual ambiguity (e.g., salads with hidden dressings vs. simple fruits) are presented to the system. This allows for the isolation of the agent's decision-making capabilities (when to ask vs. when to estimate) without the confounding variables of uncontrolled field environments.

\subsection{Phase 5: Evaluation}
The evaluation rigorously assesses the artifact against the Weighed Food Record (WFR) ground truth. We employ a quantitative experimental design to address the three research questions framed in this study:

\subsubsection{Accuracy Assessment (RQ1 \& RQ2)}
We compare the estimated energy and macronutrient values of the "Snap and Say" workflow against a baseline single-shot estimator. The primary metric is the Mean Absolute Error (MAE), defined as:
$$ MAE = \frac{1}{n} \sum_{i=1}^{n} | y_i - \hat{y}_i | $$
where $$y_i$$ represents the WFR ground truth and $$\hat{y}_i$$ represents the system contribution. We further segment this analysis by "Interaction Policy" to determine if the confidence-gated approach yields statistically significant accuracy improvements over passive vision without incurring the friction of an "always-ask" policy.

\subsubsection{Latency and Usability Analysis (RQ3)}
To ensure the solution is viable for the target demographic, we measure end-to-end system latency. Timestamps are logged at the start of image upload and the reception of the final nutritional output. Additionally, we analyze "Turn-Level Latency"—the time taken for the agent to formulate a clarifying question—comparing these against the 2-second and 10-second acceptability thresholds established in human-computer interaction literature \cite{nielsenUsabilityEngineering1994}.

\subsection{Phase 6: Communication}
The design principles, architecture, and empirical results of the "Snap and Say" system are communicated through this publication to the Information Systems and Digital Health communities.

\section{Artifact Description}

The "Snap and Say" system is implemented as a cloud-native progressive web application (PWA) designed to minimize latency and maximize accessibility for older adults.

\subsection{System Architecture}
The solution follows a modern client-server architecture:
\begin{itemize}
    \item \textbf{Frontend Client:} Built with Next.js 15.5, the interface serves as a lightweight PWA. It handles media capture (camera and microphone) and establishes a Server-Sent Events (SSE) connection to the backend for real-time agent feedback.
    \item \textbf{Backend Agent:} Hosted on FastAPI (Python 3.12), the core logic is orchestrated by LangGraph. This state machine manages the cognitive workflow, routing inputs between perception, reasoning, and clarification nodes.
    \item \textbf{Data Persistence:} Supabase (PostgreSQL) stores longitudinal dietary logs, including multimedia assets (images/audio) and structured nutritional metadata.
\end{itemize}

\subsection{Agentic Workflow Implementation}
The cognitive architecture is instantiated as a directed cyclic graph with three primary nodes:
\begin{enumerate}
    \item \textbf{Multimodal Perception Node:} This entry point utilizes OpenAI GPT-4o to process visual data (images) and auditory transcripts (Whisper-1) in parallel. It extracts food items, estimates quantities, and assigns a confidence score ($C \in [0, 1]$) to each detection.
    \item \textbf{Critique and Routing Logic:} A conditional edge applies a confidence threshold ($T=0.85$). If $C_{overall} \ge T$, the state transitions to the Finalization Node. If $C_{overall} < T$, it triggers the Clarification Node, provided the maximum turn count ($N=2$) has not been reached.
    \item \textbf{Clarification Generation Node:} Using context-aware logic, this node formulates a simplified, closed-ended question (e.g., "Is the dressing Ranch or Italian?") to resolve the specific ambiguity detected in the previous step.
\end{enumerate}

This design directly addresses the "self-auditing" requirement (FR1) by ensuring high-friction dialogue is only invoked when strictly necessary for data fidelity.

\subsection{System Semantics}
To ensure the agent behaves appropriately for a geriatric user base, the prompt engineering focuses on persona stability and accessible language. 

\textbf{Persona Instruction:} "You are a friendly dietary assistant helping seniors log their meals." 

\textbf{Critique & Guardrails:} The model is explicitly instructed to "Evaluate visibility of ingredients" and "If the image is unclear... do NOT refuse. Instead, return a valid JSON object with an empty 'items' list and a 'synthesis_comment' explaining the issue." This prevents the agent from halting the workflow due to minor visual occlusions, allowing the clarification loop to resolve ambiguity naturally.

\subsection{Structured Output Schema}
The system enforces strict syntactic correctness using Pydantic models to define the output schema. This allows the confidence logic to deterministically extract $C_{score}$ from the unstructured LLM response.

The JSON schema structure is as follows:
\begin{verbatim}
{
  "title": "string",
  "items": [
    {
      "name": "string", 
      "quantity": "string",
      "confidence": float (0.0 - 1.0)
    }
  ],
  "synthesis_comment": "string"
}
\end{verbatim}

\subsection{Model Configuration}
To balance creativity in conversation with determinism in data extraction, the system utilizes the following hyperparameters:
\begin{itemize}
    \item \textbf{Model:} GPT-4o (OpenAI)
    \item \textbf{Temperature:} Default (1.0) is maintained to allow naturalistic variation in the "synthesis_comment", while the strict JSON schema enforces structural determinism.
    \item \textbf{Context Window:} Context is scoped per-meal. Previous logs are not injected to prevent hallucination of prior meals into the current session.
\end{itemize}

\subsection{Geriatric-Centric UI Design}
The user interface implements specific affordances to mitigate age-related declines:
\begin{itemize}
    \item \textbf{Interaction Model:} The voice input utilizes a "Tap-to-Toggle" mechanic rather than "Push-to-Talk" to accommodate potential motor tremors, removing the need for sustained pressure.
    \item \textbf{Visual Feedback:} The `VoiceButton` component provides multi-sensory feedback, utilizing a dynamic waveform visualization and haptic vibration patterns (20ms/50ms) to confirm state changes without relying solely on visual acuity.
\end{itemize}

\section{Research Data Collection Schema}

\begin{table}[h]
    \centering
    \begin{tabular}{|l|l|l|}
        \hline
        \textbf{Column Name}          & \textbf{Data Type} & \textbf{Purpose}                         \\ \hline
        \texttt{log\_id}              & UUID               & Link to specific meal interaction        \\ \hline
        \texttt{input\_modality}      & Enum               & voice, photo, text (For RQ2)             \\ \hline
        \texttt{processing\_time\_ms} & Int                & Latency measurement ($< 5s$)             \\ \hline
        \texttt{agent\_turns\_count}  & Int                & Friction measurement (Intervention Rate) \\ \hline
        \texttt{was\_corrected}       & Boolean            & Error correction tracking (RQ3)          \\ \hline
        \texttt{confidence\_score}    & Float              & Internal agent confidence metric         \\ \hline
    \end{tabular}
    \caption{Schema for \texttt{research\_logs} table.}
    \label{tab:research_schema}
\end{table}