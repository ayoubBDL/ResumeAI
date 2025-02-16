from flask import Blueprint, request, jsonify
from supabase import create_client, Client
import os

# Create a Blueprint for user routes
user_routes = Blueprint('user_routes', __name__)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

@user_routes.route('/api/users/profile', methods=['PUT'])
def update_user_profile():
    """Update user profile"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "Missing X-User-Id header"
            }), 401

        data = request.get_json()
        if not data or 'full_name' not in data:
            return jsonify({
                "success": False,
                "error": "Missing full_name in request body"
            }), 400

        # Update user metadata in Supabase
        update_result = supabase.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": {"name": data['full_name']}}
        )

        if not update_result.user:
            return jsonify({
                "success": False,
                "error": "Failed to update user profile"
            }), 500

        # Get updated user data from Supabase
        user_response = supabase.auth.admin.get_user_by_id(user_id)
        if not user_response.user:
            return jsonify({
                "success": False,
                "error": "Failed to fetch updated user data"
            }), 500

        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "user_metadata": user_response.user.user_metadata,
                "app_metadata": user_response.user.app_metadata
            }
        })

    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
