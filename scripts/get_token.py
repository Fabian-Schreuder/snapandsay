import sys
from pathlib import Path

# Add backend to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / "backend"))

from supabase import create_client
from app.config import settings

def get_token():
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_ANON_KEY # Client requires Anon key for auth usually
    
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_ANON_KEY not set.")
        return

    supabase = create_client(url, key)
    
    email = "test_bench@example.com"
    password = "password123"
    
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session:
            print(res.session.access_token)
        else:
            print("No session returned.")
            
    except Exception as e:
        print(f"Error signing in: {e}")

if __name__ == "__main__":
    get_token()
