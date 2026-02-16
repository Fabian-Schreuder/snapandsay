def _clean_schema_for_google(schema: dict) -> dict:
    """
    Recursively remove 'additionalProperties' and 'title' from schema for Gemini compatibility.
    Gemini API is strict about supported JSON schema keywords.
    """
    if isinstance(schema, dict):
        new_schema = {}
        for k, v in schema.items():
            if k == "additionalProperties":
                continue
            # Remove 'title' (schema metadata), but NOT if it's a property definition named 'title'
            # However, 'title' in property definition is usually inside 'properties' -> 'title' dict.
            # The 'title' keyword in a schema object is metadata and Gemini often rejects it.
            # But we have a property named "title" in AnalysisResult!
            # The property definition is: "title": {"title": "Title", "type": "string", ...}
            # We want to keep the KEY "title" in "properties", but remove the VALUE's "title" metadata.
            if k == "title" and isinstance(v, str):
                # This captures schema metadata title (e.g. "AnalysisResult", "FoodItem")
                continue

            new_schema[k] = _clean_schema_for_google(v)
        return new_schema
    elif isinstance(schema, list):
        return [_clean_schema_for_google(item) for item in schema]
    else:
        return schema
