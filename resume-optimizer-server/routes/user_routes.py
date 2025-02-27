from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
import os

router = APIRouter()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

class ProfileUpdate(BaseModel):
    full_name: str

@router.put("/api/users/profile")
async def update_user_profile(
    profile: ProfileUpdate,
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")

    try:
        # Update user metadata in Supabase
        update_result = supabase.auth.admin.update_user_by_id(
            x_user_id,
            {"user_metadata": {"name": profile.full_name}}
        )

        if not update_result.user:
            raise HTTPException(status_code=500, detail="Failed to update user profile")

        # Get updated user data
        user_response = supabase.auth.admin.get_user_by_id(x_user_id)
        if not user_response.user:
            raise HTTPException(status_code=500, detail="Failed to fetch updated user data")

        return {
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "user_metadata": user_response.user.user_metadata,
                "app_metadata": user_response.user.app_metadata
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
