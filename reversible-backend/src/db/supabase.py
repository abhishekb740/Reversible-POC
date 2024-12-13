import supabase
import os
from dotenv import load_dotenv

load_dotenv()

supabase_client = supabase.create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)