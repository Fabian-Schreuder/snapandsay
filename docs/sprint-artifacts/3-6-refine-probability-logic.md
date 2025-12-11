# Story 3.6: Refine Probability Logic (Confidence Score/Clarification)

**Epic**: 3 - Agentic Analysis
**Status**: Ready for Dev
**Feature**: Reliability & Transparency

## Goal
Persist confidence scores and clarification reasoning to the database. This ensures we can analyze the agent's decision-making process (why it asked for clarification vs. auto-logging) and provides a confidence metric for the finalized log.

## Business Value
- **Transparency**: Allows admins/developers to see *why* a log was flagged for review or clarification.
- **Analytics**: Enables tuning of the `CONFIDENCE_THRESHOLD` based on real-world data.
- **Reliability**: Ensures that the "needs review" flag is backed by a persisted score.

## Current Limitations
- The `overall_confidence` is calculated in `AgentState` but **never saved to Supabase**.
- There is no persisted record of *why* a clarification was triggered (logic is ephemeral).

## Requirements

### 1. Database Updates
- **Table**: `dietary_logs`
- **New Column**: `confidence_score` (Type: `float` or `decimal`, nullable).
    - Stores the `overall_confidence` from the analysis.
- **New Column**: `clarification_reason` (Type: `text`, nullable).
    - Stores the reasoning for asking a clarification question (if applicable).

### 2. Backend Logic Updates (`/backend`)
- **State**: Ensure `AgentState` retains `overall_confidence` (already does).
- **Persistence (`finalize_log`, `finalize_log_streaming`)**:
    - Update the SQLAlchemy update query to include `confidence_score`.
    - Map `state["overall_confidence"]` to `dietary_logs.confidence_score`.
- **Clarification Logic**:
    - When generating a clarification, optionally capture ensuring the reasoning is clear (though the question itself implies it).
    - If "clarifying question reasoning" means "use the score to support the question", ensure the score is logged.

## Technical Tasks

### Database
- [ ] Create migration: `add_confidence_score_to_dietary_logs`.
    - File: `supabase/migrations/20251211000000_add_confidence.sql` (Use timestamp)
    - `ALTER TABLE dietary_logs ADD COLUMN confidence_score FLOAT;`
    - `ALTER TABLE dietary_logs ADD COLUMN clarification_reason TEXT;`

### Backend (`app/agent/nodes.py`)
- [ ] Update `generate_clarification` and `generate_clarification_streaming`:
    - Construct a reasoning string (e.g., "Low confidence items: Burger (0.6), Bun (0.5)").
    - Persist this `clarification_reason` to the DB when status is updated to `clarification`.
- [ ] Update `finalize_log` and `finalize_log_streaming`:
    - Ensure `overall_confidence` is saved to `dietary_logs.confidence_score`.

### Verification
- [ ] **Unit Tests**: Update `tests/app/agent/test_nodes.py` to mock DB and verify `confidence_score` is passed.
- [ ] **Manual**: Run a flow (Snap -> Analyze).
- [ ] **Check**: Verify `confidence_score` and `clarification_reason` in Supabase.

## Developer Notes
- Use raw SQL files in `supabase/migrations` as per project pattern.
- The `AgentState` already tracks `overall_confidence`.
- The threshold is defined in `constants.py`.

## Acceptance Criteria
- [ ] `dietary_logs` table includes `confidence_score`.
- [ ] Analysis flows result in a saved `confidence_score` in the database.
- [ ] Unit/Integration tests pass.
