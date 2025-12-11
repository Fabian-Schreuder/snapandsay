# Story 3.7: Multilingual Voice Support

Status: ready-for-dev

## Story

As a non-English speaking user (specifically Dutch),
I want the agent to understand my voice inputs and respond in my native language,
so that I can use the application naturally without translating my thoughts.

## Acceptance Criteria

1. **Voice Transcription:** The system correctly transcribes Dutch audio input.
2. **Language Context:** The agent detects or is configured to understand that the interaction is in Dutch.
3. **Localized Reasoning:** The LLM analyzes the Dutch transcript/input and correctly identifies food items.
4. **Localized Response:** The agent's thinking process (streamed thoughts) and clarification questions are generated in Dutch.
5. **Database Consistency:** Food items are stored in a standard format (English preferred for nutritional database matching) BUT the user-facing description/title reflects the user's language OR the system creates a localized display layer. *Note: For this story, storing in the input language (Dutch) is acceptable if nutritional lookup is not yet strictly enforcing English mapping, OR the LLM is instructed to map to English for storage while keeping Dutch for interaction.* -> **decision: Store identifying name in English for DB consistency, but keep Title/Description in User Language.**
6. **Configurable:** The language preference defaults to 'en' (English) but can be set to 'nl' (Dutch) via a new `DEFAULT_LANGUAGE` setting in `config.py`.

## Dev Notes

- **Voice Service (`app/services/voice_service.py`):**
  - Update `transcribe_audio` to accept a `language` parameter.
  - Pass this parameter to `client.audio.transcriptions.create(..., language=lang)`.
  - If no language provided, rely on Whisper's auto-detection (it is generally good for Dutch).

- **LLM Service (`app/services/llm_service.py`):**
  - Update `_build_messages` and `generate_clarification_question` logic.
  - Inject a "Language Instruction" into the System Prompt.
    - Example: "You are a dietary expert... Communicate in {language}."
    - Or: "If the input is in Dutch, reply in Dutch."
  - Ensure `synthesis_comment` and `title` are generated in the target language.
  - *Critical:* Ensure `AnalysisResult` JSON structure remains valid (keys in English, values in User Language where appropriate).

- **Agent Nodes (`app/agent/nodes.py`):**
  - Pass the language context (e.g., from `settings.DEFAULT_LANGUAGE`) to the services.
  - Add `DEFAULT_LANGUAGE` to `app/config.py` (default "en").
  - Add `DEFAULT_LANGUAGE=en` to `.env.example`.

### Project Structure Notes

- No new modules required.
- Modifies existing services (`voice_service`, `llm_service`) and agent (`nodes`).

### References

- [Voice Service](file:///home/fabian/dev/work/snapandsay/backend/app/services/voice_service.py)
- [LLM Service](file:///home/fabian/dev/work/snapandsay/backend/app/services/llm_service.py)
## Verification Plan

### Automated Tests
- **Unit Test (`tests/test_voice_service.py`):**
  - Mock `AsyncOpenAI` client.
  - Call `transcribe_audio(..., language='nl')`.
  - Assert `client.audio.transcriptions.create` was called with `language='nl'`.
- **Unit Test (`tests/test_llm_service.py`):**
  - Verify `_build_messages` includes the "Communicate in Dutch" instruction when the setting is enabled.

### Manual Verification
1. **Setup:** Set `DEFAULT_LANGUAGE=nl` in `.env`. Restart backend.
2. **Action:** Use the "Voice Capture" button in the frontend. Speak a Dutch sentence (e.g., "Ik heb een appel gegeten").
3. **Verify:**
   - The streaming text (thoughts) appears in Dutch.
   - The final response/clarification question is in Dutch.
   - The logged item title appears in the list (likely in Dutch specific to user input).
## Dev Agent Record

### Context Reference

### Agent Model Used

Gemini 2.0 Flash

### Debug Log References

### Completion Notes List

### File List
