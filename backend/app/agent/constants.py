# Node Names
ANALYZE_INPUT = "analyze_input"
GENERATE_CLARIFICATION = "generate_clarification"
FINALIZE_LOG = "finalize_log"

# SSE Event Types
EVENT_THOUGHT = "agent.thought"
EVENT_RESPONSE = "agent.response"
EVENT_ERROR = "agent.error"
EVENT_CLARIFICATION = "agent.clarification"

# Thought Step Constants
STEP_ANALYZING = "analyzing"
STEP_CLARIFYING = "clarifying"
STEP_FINALIZING = "finalizing"

# Bilingual Thought Messages
MESSAGES = {
    "en": {
        "analyzing_start": "Looking at your meal...",
        "analyzing_tokens": "Identifying ingredients...",
        "analyzing_complete": "Analysis complete",
        "clarifying": "Checking if I need more info...",
        "finalizing": "Saving your meal log...",
        "error_transcription": "I'm having trouble understanding the audio.",
        "error_no_input": "I didn't receive any image or voice input to analyze.",
        "error_analysis": "I encountered an error while analyzing your meal.",
        "error_timeout": "Processing took too long. Please try again.",
        "error_internal": "Something went wrong. Please try again.",
    },
    "nl": {
        "analyzing_start": "Ik bekijk je maaltijd...",
        "analyzing_tokens": "Ingrediënten herkennen...",
        "analyzing_complete": "Analyse voltooid",
        "clarifying": "Ik kijk of ik meer info nodig heb...",
        "finalizing": "Je maaltijd wordt opgeslagen...",
        "error_transcription": "Ik heb moeite om de audio te begrijpen.",
        "error_no_input": "Ik heb geen foto of spraak ontvangen om te analyseren.",
        "error_analysis": "Er is een fout opgetreden bij het analyseren van je maaltijd.",
        "error_timeout": "Het verwerken duurde te lang. Probeer het opnieuw.",
        "error_internal": "Er is iets misgegaan. Probeer het opnieuw.",
    },
}

# Legacy constants for backward compatibility
MSG_ANALYZING_START = MESSAGES["nl"]["analyzing_start"]
MSG_ANALYZING_TOKENS = MESSAGES["nl"]["analyzing_tokens"]
MSG_ANALYZING_COMPLETE = MESSAGES["nl"]["analyzing_complete"]
MSG_CLARIFYING = MESSAGES["nl"]["clarifying"]
MSG_FINALIZING = MESSAGES["nl"]["finalizing"]


def get_message(key: str, language: str = "nl") -> str:
    """Get a localized message by key and language code."""
    lang_messages = MESSAGES.get(language, MESSAGES["nl"])
    return lang_messages.get(key, key)


# Confidence Routing Constants
CONFIDENCE_THRESHOLD = 0.85
MAX_CLARIFICATIONS = 2
CLARIFICATION_TIMEOUT_SECONDS = 30
