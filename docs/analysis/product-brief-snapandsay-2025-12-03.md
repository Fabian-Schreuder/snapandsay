---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'product-brief'
lastStep: 0
project_name: 'snapandsay'
user_name: 'Fabian'
date: '2025-12-03'
---

# Product Brief: snapandsay

**Date:** 2025-12-03
**Author:** Fabian

---

## 1. Executive Summary

Snap and Say addresses the critical "Friction-Fidelity Trade-off" in dietary assessment, specifically targeting older adults (65+) managing chronic conditions. Current solutions force a choice between high-effort manual logging or low-accuracy automated AI. Snap and Say bridges this gap using **Agentic AI** to enable conversational, voice-first logging. Instead of passive guessing, the system actively reasons and engages the user ("I can't see the dressing") to ensure medical-grade data fidelity without user fatigue. This approach solves the "Cold Start" problem and empowers clinicians with accurate, structured nutritional data.

---

## 2. Core Vision

### Problem Statement
Existing dietary tracking tools fail to balance ease-of-use with data accuracy. Manual logging is too burdensome for non-tech-savvy older adults, leading to abandonment, while current automated AI vision tools lack the reasoning capabilities to capture hidden ingredients or portion nuances, resulting in "Garbage In, Garbage Out" for clinicians.

### Problem Impact
- **Users (65+):** Frustration with complex UIs, tiny buttons, and "interrogation" style apps leads to tracking fatigue and disengagement.
- **Clinicians/Researchers:** Reliance on incomplete or inaccurate data compromises treatment plans and research validity for chronic conditions like diabetes and hypertension.

### Why Existing Solutions Fall Short
- **Manual Apps:** Require high cognitive load (searching, weighing, typing) and complex navigation.
- **Passive AI:** "Input Image -> Output Guess" models fail on visual ambiguity and cannot correct themselves, leading to low trust and poor data quality.

### Proposed Solution
A "Conversational Logging" tool where users simply take a photo and speak naturally ("I had this, but didn't eat the crust"). The system uses **Agentic AI** to process the input, reason about missing details, and proactively ask clarifying questions only when needed. This feels like "telling a friend" rather than data entry.

### Key Differentiators
- **Agentic vs. Passive AI:** The system reasons and asks questions to resolve ambiguity, rather than just guessing.
- **No "Cold Start" Constraint:** Does not require a perfect universal food model; relies on interactive reasoning to handle unknown items.
- **Age-Tech Focus:** Designed specifically for accessibility, removing friction (typing, searching) for older adults.

## 3. Target Users

### Primary Users

#### 1. Martha (The "Casual" User)
*   **Profile**: 72, lives alone, widow. Uses an iPad for FaceTime but finds "apps" confusing.
*   **Motivation**: Wants to maintain independence and keep her doctor happy, but struggles with the "admin" of tracking.
*   **Pain Point**: Forgets to log meals; finds writing things down tedious; lonely.
*   **Success**: "I just talk to it like a friend, and my doctor says I'm doing great."

#### 2. Robert (The "Medical" User)
*   **Profile**: 68, Type 2 Diabetic, retired engineer. Meticulous but frustrated by "dumb" tools.
*   **Motivation**: Needs precise control over blood sugar.
*   **Pain Point**: Generic apps don't understand the correlation between his food and his glucose readings.
*   **Success**: "It catches things I miss. It reminded me that the sauce had hidden sugar."

### Secondary Users

*   **Dr. Chen (The Clinician)**: Needs accurate, summarized longitudinal data (trends, not just data points) to adjust care plans.
*   **"The Worried Child" (Family)**: Wants peace of mind that their parent is eating well without having to nag them personally.

### User Journey: Martha's "Gentle Nudge"

1.  **Discovery**: Martha's daughter installs the app. "Mom, just talk to this, it's easier."
2.  **Onboarding**: No complex signup. The Agent simply introduces itself: "Hi Martha, I'm here to help you keep track of things. What did you have for breakfast?"
3.  **Core Usage (The "Cold Start" Fix)**:
    *   *1:00 PM*: Martha is watching TV.
    *   *Agent*: (Chimes gently) "Hi Martha, I noticed you haven't logged lunch yet. Did you have that soup?"
    *   *Martha*: "No, I made a sandwich."
    *   *Agent*: "Turkey and cheese?"
    *   *Martha*: "Yes, with a little mayo."
    *   *Agent*: "Got it. Sounds delicious." (Logs: Turkey Sandwich, 1 tbsp Mayo).
4.  **Success Moment**: At her next checkup, Dr. Chen shows her a graph. "Martha, your protein intake is up 20% this month. Keep it up!" Martha beams—she didn't "work" for this.

## 4. Success Metrics

### North Star Metric
**"Verified Nutritional Data Points (VNDP) per User"**
*   **Definition**: The count of nutritional data points (calories, macros) that have been explicitly confirmed or clarified through the Agent-User loop.
*   **Why**: Combines Adoption (logging), Effectiveness (structuring data), and Accuracy (verification). Unlike DAU, this measures the generation of **Science-Ready Data**.

### User Success: "Martha's Experience"
For the primary user, success is about **feeling heard and unburdened**, not just data entry.
*   **The "Zero-Friction" Test**: Martha should never have to search for items in a dropdown.
*   **The Trust Indicator**: Clarifying questions should feel helpful ("Was that regular or diet?"), not annoying.
*   **Success Statement**: "I talk to it like a person, and it remembers what I ate better than I do."

### Business & System Objectives
We are building a **Data Generation Engine** to prove the "Relational Foundation" approach.

| Metric Category | Metric | Why it matters |
| :--- | :--- | :--- |
| **Data Quality** | **Structured Data Yield**<br>*(% of logs resulting in valid SQL)* | Proves the Agentic Loop works. |
| **Feasibility** | **Autonomous Resolution Rate**<br>*(% of logs handled without abandonment)* | Validates the "Agent" capabilities in real-world messiness. |
| **Retention** | **Day-30 Retention Rate** | Critical for solving the "Cold Start" problem and generating longitudinal datasets. |

## 5. MVP Scope (Research MVP)

**Goal**: Prove the *Agentic Data Collection* thesis in a 3-month timeline. NOT a commercial App Store launch.

### 2. Core Features (The "Must-Haves")
*   **Interface (Mobile Web/PWA):**
    *   Camera Capture (Photo of meal).
    *   Voice Recorder (Audio description) with **Text Input Fallback** (critical if audio fails).
    *   Simple Chat Interface (Streamlit-based).
*   **"Agentic" Brain (Backend):**
    *   **Merged Prompt Logic:** Single LLM call to analyze image/audio. Output JSON: `{ status: 'clarify', question: '...' }` OR `{ status: 'complete', data: ... }`. Reduces latency.
    *   **1-Turn Limit:** Agent asks *one* clarifying question max. If ambiguous after that, log as "Unverified" and move on. No infinite loops.
*   **Relational Sink (Database):**
    *   Structured Output (JSON -> SQL schema).
    *   Persistent Storage (Supabase).

### Out of Scope (The "Not Now" List)
*   **$\times$ Complex Authentication**: No OAuth. Simple User ID only.
*   **$\times$ Clinician Dashboard**: Raw Data Export (CSV/SQL) only.
*   **$\times$ External Integrations**: No Apple Health/Fitbit.
*   **$\times$ Gamification/Social**: No streaks, no sharing.
*   **$\times$ Meal Plans/Recipes**: Analysis only, no advice.

### The Walking Skeleton
*The smallest possible implementation that functions end-to-end.*
1.  **INPUT**: User clicks "Log Meal", takes photo of sandwich, says nothing.
2.  **PROCESSING**: Agent sees sandwich, Gap Detector notes missing filling.
3.  **FEEDBACK**: UI asks: *"I see a sandwich. What kind of meat or filling is inside?"*
4.  **RE-INPUT**: User records: *"It's ham and cheese."*
5.  **STORAGE**: System saves `Item: Ham and Cheese Sandwich`, `Bread: White`, `Filling: Ham, Cheese`.
6.  **COMPLETION**: App shows green checkmark.

### Technology Stack (Speed-Focused)
*   **Frontend**: **Streamlit** (Python) - Mobile browser compatible, handles camera/audio, no complex state.
*   **Backend Logic**: **LangChain** (Python) - Manages Agentic state.
*   **AI Model**: **OpenAI GPT-4o** - Native multimodal + JSON enforcement.
*   **Database**: **Supabase** (PostgreSQL) - Free, SQL, easy interface.
