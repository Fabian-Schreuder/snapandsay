
import csv
import json
import io
from typing import List, Generator, Any
from app.models.log import DietaryLog

def export_logs_as_csv(logs: List[DietaryLog]) -> Generator[str, None, None]:
    """
    Export logs to CSV format.
    Returns a generator of CSV strings.
    """
    header = ["Log ID", "User Email", "Meal Type", "Food Items", "Calories", "Created At", "Transcription"]
    
    output = io.StringIO()
    # csv module doesn't strictly support async/generators well with writer, 
    # but we can write one row at a time.
    writer = csv.writer(output)
    
    # Write Header with BOM for Excel compatibility
    writer.writerow(header)
    yield '\ufeff' + output.getvalue()
    output.seek(0)
    output.truncate(0)

    for log in logs:
        # Determine User Email
        user_email = "Unknown"
        if hasattr(log, "user") and log.user and hasattr(log.user, "email"):
            user_email = log.user.email
        
        # Determine Meal Type
        meal_type = log.meal_type or "Unknown"
        
        row = [
            str(log.id),
            user_email,
            meal_type,
            log.description or "",
            log.calories or 0,
            log.created_at.isoformat() if log.created_at else "",
            log.transcript or ""
        ]
        
        writer.writerow(row)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

def export_logs_as_json(logs: List[DietaryLog]) -> Generator[str, None, None]:
    """
    Export logs to JSON format.
    Returns a generator of JSON strings (streaming array).
    """
    yield "["
    first = True
    for log in logs:
        if not first:
            yield ","
        first = False
        
        user_email = "Unknown"
        if hasattr(log, "user") and log.user and hasattr(log.user, "email"):
            user_email = log.user.email

        data = {
            "id": str(log.id),
            "user_email": user_email,
            "meal_type": log.meal_type or "Unknown",
            "food_items": log.description,
            "calories": log.calories,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "transcript": log.transcript,
            "protein": log.protein,
            "carbs": log.carbs,
            "fats": log.fats,
            "image_path": log.image_path,
            "status": log.status
        }
        yield json.dumps(data)
    yield "]"
