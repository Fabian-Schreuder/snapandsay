import json

from app.schemas.analysis import AnalysisResult
from app.services.llm_service import _clean_schema_for_google

schema = AnalysisResult.model_json_schema()
cleaned = _clean_schema_for_google(schema)
print(json.dumps(cleaned, indent=2))
