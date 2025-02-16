from flask import Blueprint, request, jsonify
from supabase import create_client, Client
import os
import base64
from dotenv import load_dotenv
import os
import openai
import requests
import json
import io
import base64
import pdfplumber
from flask import Flask, request, jsonify, make_response, send_file
from services.supabase_client import supabase
from reportlab.lib import colors

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle, HRFlowable
import re
import tempfile
import time
from bs4 import BeautifulSoup
from supabase import create_client, Client
import datetime
import logging
from flask import Flask, request, jsonify, make_response, send_file
from flask_cors import CORS
from requests.auth import HTTPBasicAuth
from waitress import serve 


# Create a Blueprint for subscription routes
subscription_routes = Blueprint('subscription_routes', __name__)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

@subscription_routes.route('/api/credits', methods=['GET'])
def get_user_credits():
    """Get user's current credit balance"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        credits_response = supabase.table('usage_credits').select('credits_remaining').eq('user_id', user_id).execute()
        if len(credits_response.data) == 0:
            # Create initial credits for user if not exists
            supabase.table('usage_credits').insert({
                'user_id': user_id,
                'credits_remaining': 2,
                'created_at': datetime.datetime.utcnow().isoformat(),
                'updated_at': datetime.datetime.utcnow().isoformat()
            }).execute()
            return jsonify({"credits": 2})

        return jsonify({
            "credits": credits_response.data[0]['credits_remaining']
        })

    except Exception as e:
        print(f"Error getting user credits: {str(e)}")
        return jsonify({"error": "Failed to get user credits"}), 500

@subscription_routes.route('/api/credits/initialize', methods=['POST'])
def initialize_credits():
    """Initialize credits for a new user"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        # Check if user already has credits
        credits_response = supabase.table('usage_credits').select('credits_remaining').eq('user_id', user_id).execute()
        if len(credits_response.data) > 0:
            return jsonify({"error": "Credits already initialized for this user"}), 400

        # Initialize credits for new user
        supabase.table('usage_credits').insert({
            'user_id': user_id,
            'credits_remaining': 2,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'updated_at': datetime.datetime.utcnow().isoformat()
        }).execute()

        return jsonify({
            "success": True,
            "message": "Credits initialized successfully",
            "credits": 2
        })

    except Exception as e:
        print(f"Error initializing credits: {str(e)}")
        return jsonify({"error": "Failed to initialize credits"}), 500

@subscription_routes.route('/api/credits/purchase', methods=['POST'])
def purchase_credits():
    """Purchase credits based on selected plan"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        data = request.get_json()

        # Calculate credits based on plan
        min_credits = 5
        requested_credits = data.get('credits', min_credits)
        if requested_credits < min_credits:
            return jsonify({"error": f"Minimum credit purchase is {min_credits}"}), 400
        credits = requested_credits

        # Get current credits
        credits_response = supabase.table('usage_credits').select('credits_remaining').eq('user_id', user_id).execute()
        print("Credits response:", credits_response)

        if not credits_response.data:
            # Create new record if it doesn't exist
            new_credits = credits
            supabase.table('usage_credits').insert({
                'user_id': user_id,
                'credits_remaining': new_credits
            }).execute()
        else:
            # Update existing record
            current_credits = credits_response.data[0]['credits_remaining']
            new_credits = current_credits + credits
            print(f"Updating credits from {current_credits} to {new_credits}")
            supabase.table('usage_credits').update({
                'credits_remaining': new_credits
            }).eq('user_id', user_id).execute()

        return jsonify({
            "success": True,
            "message": f"Successfully added {credits} credits",
            "new_balance": new_credits
        })

    except Exception as e:
        print(f"Error purchasing credits: {str(e)}")
        return jsonify({"error": "Failed to purchase credits"}), 500

@subscription_routes.route('/api/subscriptions', methods=['GET'])
def get_subscription():
    """Get user's current subscription status"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        # Get subscription from Supabase - now without status filter
        subscription_response = supabase.table('subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()

        # If no subscription found at all, return early
        if not subscription_response.data or len(subscription_response.data) == 0:
            return jsonify({
                "has_subscription": False,
                "subscription": None
            })

        # Get the subscription data
        subscription = subscription_response.data[0]
        paypal_subscription_id = subscription.get('paypal_subscription_id')

        # If no PayPal subscription ID, return just the Supabase data
        if not paypal_subscription_id:
            return jsonify({
                "has_subscription": subscription.get('status') == 'active',
                "subscription": subscription
            })

        # Check PayPal status only if subscription was active
        if subscription.get('status') == 'active':
            access_token = generate_paypal_token()
            if not access_token:
                return jsonify({"error": "Failed to generate Paypal access token"}), 500

            url = f"{os.getenv('PAYPAL_API_URL')}/v1/billing/subscriptions/{paypal_subscription_id}"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
            
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                paypal_status = response.json().get('status', '').lower()
                
                # If cancelled in PayPal but active in Supabase, update Supabase
                if paypal_status in ['cancelled', 'suspended', 'expired']:
                    now = datetime.datetime.utcnow()
                    supabase.table('subscriptions')\
                        .update({
                            'status': paypal_status,
                            'updated_at': now.isoformat(),
                            'cancelled_at': now.isoformat()
                        })\
                        .eq('id', subscription.get('id'))\
                        .execute()

                    return jsonify({
                        "has_subscription": False,
                        "subscription": subscription,
                        "paypal_subscription": response.json()
                    })

            return jsonify({
                "has_subscription": True,
                "subscription": subscription,
                "paypal_subscription": response.json()
            })
        
        # For inactive subscriptions, just return the data without PayPal check
        return jsonify({
            "has_subscription": False,
            "subscription": subscription
        })

    except Exception as e:
        print(f"Error getting subscription: {str(e)}")
        return jsonify({"error": "Failed to get subscription status"}), 500

@subscription_routes.route('/api/subscriptions', methods=['POST'])
def create_subscription():
    """Create or update user subscription"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        data = request.get_json()
        if not data or 'plan_type' not in data:
            return jsonify({"error": "Plan type is required"}), 400

        if not data or 'subscriptionId' not in data:
            return jsonify({"error": "subscriptionId is required"}), 400

        plan_type = data['plan_type']
        
        # Cancel any existing active subscriptions
        supabase.table('subscriptions')\
            .update({'status': 'cancelled'})\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()

        # Create new subscription
        now = datetime.datetime.utcnow()
        subscription_data = {
            'user_id': user_id,
            'plan_type': plan_type,
            'paypal_subscription_id': data['subscriptionId'],
            'status': 'active',
            'current_period_start': now.isoformat(),
            'current_period_end': (now + datetime.timedelta(days=30)).isoformat(),
            'created_at': now.isoformat(),
            'updated_at': now.isoformat()
        }

        subscription_result = supabase.table('subscriptions')\
            .insert(subscription_data)\
            .execute()

        # Update user credits based on plan
        credits = supabase.table('usage_credits').select('credits_remaining').eq('user_id', user_id).execute()
        if plan_type == 'pro':
            credits = credits.data[0]['credits_remaining'] + 50
        elif plan_type == 'yearly':
            credits = credits.data[0]['credits_remaining'] + 9999
        elif plan_type == 'enterprise':
            credits = credits.data[0]['credits_remaining'] + 999999

        # Update or create credits
        credits_response = supabase.table('usage_credits').select('*').eq('user_id', user_id).execute()
        if len(credits_response.data) == 0:
            supabase.table('usage_credits').insert({
                'user_id': user_id,
                'credits_remaining': credits,
                'created_at': now.isoformat(),
                'updated_at': now.isoformat()
            }).execute()
        else:
            supabase.table('usage_credits').update({
                'credits_remaining': credits,
                'updated_at': now.isoformat()
            }).eq('user_id', user_id).execute()

        return jsonify({
            "success": True,
            "message": f"Successfully subscribed to {plan_type} plan",
            "subscription": subscription_result.data[0] if subscription_result.data else None,
            "credits": credits
        })

    except Exception as e:
        print(f"Error creating subscription: {str(e)}")
        return jsonify({"error": "Failed to create subscription"}), 500

@subscription_routes.route('/api/cancel-subscription', methods=['POST'])
def cancel_subscription():
    """Cancel user subscription"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({
                "success": False,
                "error": "User ID is required"
            }), 401

        # Get the active subscription for the user
        subscription_result = supabase.table('subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('status', 'active')\
            .execute()

        if not subscription_result.data:
            return jsonify({
                "success": False,
                "error": "No active subscription found"
            }), 404

        subscription = subscription_result.data[0]
        subscription_id = subscription.get('id')
        paypal_subscription_id = subscription.get('paypal_subscription_id')

        if not subscription_id:
            return jsonify({
                "success": False,
                "error": "Invalid subscription ID"
            }), 400

        if not paypal_subscription_id:
            return jsonify({
                "success": False,
                "error": "No PayPal subscription ID found"
            }), 400

        # Generate PayPal access token
        try:
            access_token = generate_paypal_token()
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Failed to generate PayPal token: {str(e)}"
            }), 500

        # First check subscription status in PayPal
        status_url = f"{os.getenv('PAYPAL_API_URL')}/v1/billing/subscriptions/{paypal_subscription_id}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        status_response = requests.get(status_url, headers=headers)
        print("PayPal Status Response:", status_response.json())

        if status_response.status_code == 200:
            paypal_status = status_response.json().get('status', '').lower()
            
            # If already cancelled in PayPal, just update Supabase
            if paypal_status in ['cancelled', 'suspended', 'expired']:
                now = datetime.datetime.utcnow()
                supabase.table('subscriptions')\
                    .update({
                        'status': 'cancelled',
                        'updated_at': now.isoformat(),
                        'cancelled_at': now.isoformat()
                    })\
                    .eq('id', subscription_id)\
                    .execute()

                return jsonify({
                    "success": True,
                    "message": "Subscription status synchronized with PayPal"
                })

        # If not cancelled, proceed with cancellation
        cancel_url = f"{os.getenv('PAYPAL_API_URL')}/v1/billing/subscriptions/{paypal_subscription_id}/cancel"
        cancel_response = requests.post(
            cancel_url,
            headers=headers,
            json={"reason": "Cancelled by user"}
        )

        print("PAYPAL REQUEST", cancel_url)
        print("PAYPAL RESPONSE STATUS", cancel_response.status_code)
        print("PAYPAL RESPONSE CONTENT", cancel_response.content)

        if cancel_response.status_code not in [204, 200]:
            return jsonify({
                "success": False,
                "error": f"Failed to cancel PayPal subscription. Status: {cancel_response.status_code}"
            }), 500

        # Update subscription status in Supabase
        now = datetime.datetime.utcnow()
        supabase.table('subscriptions')\
            .update({
                'status': 'cancelled',
                'updated_at': now.isoformat(),
                'cancelled_at': now.isoformat()
            })\
            .eq('id', subscription_id)\
            .execute()

        return jsonify({
            "success": True,
            "message": "Subscription cancelled successfully"
        })

    except Exception as e:
        print(f"Error cancelling subscription: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def check_user_credits(user_id):
    """Check if user has credits in Supabase"""
    try:
        credits_response = supabase.table('usage_credits')\
            .select('credits_remaining')\
            .eq('user_id', user_id)\
            .execute()
            
        # If no credits record exists or credits <= 0
        if len(credits_response.data) == 0 or credits_response.data[0]['credits_remaining'] <= 0:
            return False, {
                "error": "Insufficient credits",
                "message": "You have no credits remaining. Please purchase more credits to continue.",
                "action": "purchase_required",
                "redirect_url": "/dashboard/billing",
                "current_credits": credits_response.data[0]['credits_remaining'] if credits_response.data else 0
            }

        return True, credits_response.data[0]['credits_remaining']

    except Exception as e:
        print(f"Error checking user credits: {str(e)}")
        return False, {"error": "Failed to check credits"}

@subscription_routes.route('/api/create-paypal-subscription', methods=['POST'])
def create_paypal_subscription():
    """Create or update user subscription"""
    try:
        user_id = request.headers.get('X-User-Id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 401

        data = request.get_json()
        if not data or 'plan_id' not in data:
            return jsonify({"error": "Plan ID is required"}), 400
        if not data or 'access_token' not in data:
            return jsonify({"error": "access_token is required"}), 400
        plan_id = data['plan_id']
        access_token = data['access_token']
        
        url = f'https://api-m.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}'

        if not access_token:
            return jsonify({"error": "Failed to generate Paypal access token"}), 500
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Prefer': 'return=representation',
            'Authorization': f'Bearer {access_token}',
            'PayPal-Request-Id': 'SUBSCRIPTION-21092019-001',
        }

        body = {
            "plan_id": plan_id,
            "start_time": "2025-10-20T12:00:00Z",
            "application_context": {
                "user_action": "SUBSCRIBE_NOW",
                "return_url": "https://localhost:5173/success",
                "cancel_url": "https://localhost:5173/cancel"
            }
        }

        response = requests.post(url, headers=headers, json=body)

        if response.status_code != 201:
            return jsonify({"error": "Failed to create subscription"}), 500

        return jsonify({
            "success": True,
            "subscription": response.json()
        })

    except Exception as e:
        print(f"Error creating subscription: {str(e)}")
        return jsonify({"error": "Failed to create subscription"}), 500

def generate_paypal_token() -> str:
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise Exception("Missing PayPal client ID or secret in environment variables.")
    
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_header}",
    }
    
    response = requests.post(url, headers=headers, data="grant_type=client_credentials")
    
    if response.status_code == 200:
        return response.json().get("access_token", "")
    else:
        raise Exception(f"Failed to generate token: {response.status_code}, {response.text}")

