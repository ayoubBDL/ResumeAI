import os
from dotenv import load_dotenv
from supabase import create_client, Client
from pathlib import Path

# Load environment variables from the root directory's .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    raise ValueError(f"Supabase URL and key must be set in environment variables. Looking for .env at: {env_path}")

supabase: Client = create_client(supabase_url, supabase_key)
