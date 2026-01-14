import os
import sys
from pathlib import Path

# Add backend to path so we can import app.config
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "backend"))

from supabase import create_client, Client

from app.config import settings

def create_test_user():
    print("Initializing Supabase Admin Client...")
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set.")
        return

    supabase: Client = create_client(url, key)
    
    email = "test_bench@example.com"
    password = "password123"
    
    print(f"Checking/Creating user: {email}")
    
    try:
        attributes = {"email": email, "password": password, "email_confirm": True}
        user = supabase.auth.admin.create_user(attributes)
        print(f"User created: {user.user.id}")
            
    except Exception as e:
        if "User already registered" in str(e) or "duplicate key" in str(e):
            print("User already exists. Proceeding...")
        else:
            print(f"Error creating user: {e}")

if __name__ == "__main__":
    create_test_user()
