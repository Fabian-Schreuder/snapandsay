import json

from app.schemas.analysis import AnalysisResult

schema = AnalysisResult.model_json_schema()
print(json.dumps(schema, indent=2))
