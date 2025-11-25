"""
Sellauth Integration - Flask Web Application
Provides the same SMB Panel functionality as the Discord bot but for Sellauth website
"""
import os
import hmac
import hashlib
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timezone
import logging
import sys

# Import local modules
from smb_panel import SMBApiClient
from redeem_db import RedeemDatabase
from link_validator import LinkValidator

# Load environment variables from .env file or environment
load_dotenv()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SellauthApp')

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-key-in-production')
CORS(app)

# Initialize SMB Panel API client
smb_client = SMBApiClient(api_key=os.getenv('SMBPANEL_API_KEY'))

# Initialize Redeem Database
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'redeem_codes.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
redeem_db = RedeemDatabase(db_path)

# Configuration
SELLAUTH_WEBHOOK_SECRET = os.getenv('SELLAUTH_WEBHOOK_SECRET', '')
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', '')
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')

# Helper functions
def verify_sellauth_webhook(payload, signature):
    """Verify Sellauth webhook signature"""
    if not SELLAUTH_WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured")
        return True  # Allow in dev mode
    
    expected_signature = hmac.new(
        SELLAUTH_WEBHOOK_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

def verify_admin_key(api_key):
    """Verify admin API key"""
    if not ADMIN_API_KEY:
        return False
    return hmac.compare_digest(api_key, ADMIN_API_KEY)

def create_response(success=True, message="", data=None):
    """Create standardized API response"""
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    if data:
        response['data'] = data
    return jsonify(response)

# Routes
@app.route('/')
def index():
    """Home page with redemption form"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin dashboard"""
    return render_template('admin.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return create_response(True, "Service is running")

@app.route('/api/services', methods=['GET'])
def get_services():
    """Get all available SMB Panel services"""
    try:
        services_list = smb_client.get_services()
        
        if not services_list or 'error' in services_list:
            return create_response(False, "Failed to fetch services", {'error': services_list.get('error', 'Unknown error')})
        
        # Group by category
        categories = {}
        for service in services_list:
            category = service.get('category', 'Uncategorized')
            if category not in categories:
                categories[category] = []
            categories[category].append(service)
        
        return create_response(True, "Services fetched successfully", {
            'services': services_list,
            'categories': categories,
            'total': len(services_list)
        })
    except Exception as e:
        logger.error(f"Error fetching services: {e}")
        return create_response(False, str(e)), 500

@app.route('/api/search', methods=['POST'])
def search_services():
    """Search for services with filters"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        max_price = data.get('max_price')
        min_quantity = data.get('min_quantity')
        max_quantity = data.get('max_quantity')
        refill_only = data.get('refill_only', False)
        no_drop = data.get('no_drop', False)
        
        services_list = smb_client.get_services()
        
        if not services_list or 'error' in services_list:
            return create_response(False, "Failed to fetch services")
        
        # Search and filter
        query_words = query.split()
        matching_services = []
        
        for service in services_list:
            name = service.get('name', '').lower()
            category = service.get('category', '').lower()
            service_type = service.get('type', '').lower()
            searchable_text = f"{name} {category} {service_type}"
            
            # Check query match
            if query and not all(word in searchable_text for word in query_words):
                continue
            
            # Price filter
            if max_price is not None:
                try:
                    if float(service.get('rate', 999999)) > max_price:
                        continue
                except:
                    continue
            
            # Quantity filters
            if min_quantity is not None:
                try:
                    if int(service.get('min', 0)) > min_quantity:
                        continue
                except:
                    continue
            
            if max_quantity is not None:
                try:
                    if int(service.get('max', 0)) < max_quantity:
                        continue
                except:
                    continue
            
            # Refill filter
            if refill_only and not service.get('refill', False):
                continue
            
            # No drop filter
            if no_drop:
                name_lower = service.get('name', '').lower()
                has_no_drop = any(keyword in name_lower for keyword in [
                    'no drop', 'nodrop', 'no-drop', 'permanent', 'lifetime', 
                    'guaranteed', 'guarantee', 'stable'
                ])
                if not has_no_drop:
                    continue
            
            matching_services.append(service)
        
        # Sort by price
        matching_services.sort(key=lambda x: float(x.get('rate', 999999)))
        
        return create_response(True, f"Found {len(matching_services)} services", {
            'services': matching_services,
            'count': len(matching_services)
        })
    except Exception as e:
        logger.error(f"Error searching services: {e}")
        return create_response(False, str(e)), 500

@app.route('/api/redeem', methods=['POST'])
def redeem_code():
    """Redeem a code and create SMB Panel order"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        link = data.get('link', '').strip()
        user_id = data.get('user_id', 'web_user')
        username = data.get('username', 'Web User')
        
        if not code or not link:
            return create_response(False, "Code and link are required")
        
        # Validate code
        is_valid, message = redeem_db.is_code_valid(code)
        if not is_valid:
            return create_response(False, message)
        
        # Get code details
        code_data = redeem_db.get_code(code)
        
        # Validate link
        is_link_valid, link_message = LinkValidator.detect_link_type(
            link, 
            code_data['platform'], 
            code_data['service_type']
        )
        
        if not is_link_valid:
            return create_response(False, link_message)
        
        # Create order on SMB Panel
        order_result = smb_client.create_order(
            service_id=code_data['service_id'],
            link=link,
            quantity=code_data['quantity']
        )
        
        if 'order' not in order_result:
            return create_response(False, f"Failed to create order: {order_result.get('error', 'Unknown error')}")
        
        order_id = order_result['order']
        
        # Mark code as used
        redeem_db.mark_code_used(code, user_id, order_id)
        
        # Add to redemption history
        redeem_db.add_redemption_history(
            code=code,
            user_id=user_id,
            username=username,
            service_id=code_data['service_id'],
            quantity=code_data['quantity'],
            link=link,
            order_id=order_id
        )
        
        logger.info(f"Code redeemed: {code} by {username} (Order: {order_id})")
        
        return create_response(True, "Code redeemed successfully!", {
            'order_id': order_id,
            'service_id': code_data['service_id'],
            'quantity': code_data['quantity'],
            'platform': code_data['platform'],
            'service_type': code_data['service_type'],
            'has_refill': code_data.get('has_refill', False)
        })
        
    except Exception as e:
        logger.error(f"Error redeeming code: {e}")
        return create_response(False, str(e)), 500

@app.route('/api/validate-code', methods=['POST'])
def validate_code():
    """Validate a code without redeeming it"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        
        if not code:
            return create_response(False, "Code is required")
        
        is_valid, message = redeem_db.is_code_valid(code)
        
        if is_valid:
            code_data = redeem_db.get_code(code)
            return create_response(True, "Code is valid", {
                'platform': code_data['platform'],
                'service_type': code_data['service_type'],
                'quantity': code_data['quantity'],
                'requirements': code_data.get('requirements', ''),
                'has_refill': code_data.get('has_refill', False)
            })
        else:
            return create_response(False, message)
            
    except Exception as e:
        logger.error(f"Error validating code: {e}")
        return create_response(False, str(e)), 500

@app.route('/api/user/redemptions', methods=['POST'])
def get_user_redemptions():
    """Get redemption history for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return create_response(False, "User ID is required")
        
        redemptions = redeem_db.get_user_redemptions(user_id)
        
        return create_response(True, f"Found {len(redemptions)} redemptions", {
            'redemptions': redemptions,
            'count': len(redemptions)
        })
        
    except Exception as e:
        logger.error(f"Error fetching redemptions: {e}")
        return create_response(False, str(e)), 500

# Admin endpoints (require API key)
@app.route('/api/admin/balance', methods=['GET'])
def admin_balance():
    """Get SMB Panel balance (admin only)"""
    api_key = request.headers.get('X-API-Key')
    
    if not verify_admin_key(api_key):
        return create_response(False, "Unauthorized"), 401
    
    try:
        balance_data = smb_client.get_balance()
        return create_response(True, "Balance fetched", balance_data)
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        return create_response(False, str(e)), 500

@app.route('/api/admin/order', methods=['POST'])
def admin_create_order():
    """Create order directly (admin only)"""
    api_key = request.headers.get('X-API-Key')
    
    if not verify_admin_key(api_key):
        return create_response(False, "Unauthorized"), 401
    
    try:
        data = request.get_json()
        service_id = data.get('service_id')
        link = data.get('link')
        quantity = data.get('quantity')
        
        if not all([service_id, link, quantity]):
            return create_response(False, "Missing required fields")
        
        result = smb_client.create_order(service_id, link, quantity)
        
        if 'order' in result:
            return create_response(True, "Order created", result)
        else:
            return create_response(False, result.get('error', 'Unknown error'))
            
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return create_response(False, str(e)), 500

@app.route('/api/admin/codes', methods=['GET'])
def admin_get_codes():
    """Get all codes (admin only)"""
    api_key = request.headers.get('X-API-Key')
    
    if not verify_admin_key(api_key):
        return create_response(False, "Unauthorized"), 401
    
    try:
        status = request.args.get('status')
        codes = redeem_db.get_all_codes(status)
        
        return create_response(True, f"Found {len(codes)} codes", {
            'codes': codes,
            'count': len(codes)
        })
    except Exception as e:
        logger.error(f"Error fetching codes: {e}")
        return create_response(False, str(e)), 500

@app.route('/api/admin/redemptions', methods=['GET'])
def admin_get_redemptions():
    """Get all redemptions (admin only)"""
    api_key = request.headers.get('X-API-Key')
    
    if not verify_admin_key(api_key):
        return create_response(False, "Unauthorized"), 401
    
    try:
        redemptions = redeem_db.get_all_redemptions()
        
        return create_response(True, f"Found {len(redemptions)} redemptions", {
            'redemptions': redemptions,
            'count': len(redemptions)
        })
    except Exception as e:
        logger.error(f"Error fetching redemptions: {e}")
        return create_response(False, str(e)), 500

# Sellauth webhook endpoint
@app.route('/webhook/sellauth', methods=['POST'])
def sellauth_webhook():
    """Handle Sellauth webhooks for automatic code delivery"""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Sellauth-Signature', '')
        payload = request.get_data(as_text=True)
        
        if not verify_sellauth_webhook(payload, signature):
            logger.warning("Invalid webhook signature")
            return create_response(False, "Invalid signature"), 401
        
        data = request.get_json()
        event_type = data.get('event')
        
        logger.info(f"Received Sellauth webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'order.completed':
            # Customer completed purchase - deliver code
            customer_email = data.get('customer', {}).get('email')
            product_id = data.get('product', {}).get('id')
            order_id = data.get('order_id')
            
            # Here you would:
            # 1. Look up which service this product corresponds to
            # 2. Generate or assign a code
            # 3. Send code to customer via email or Sellauth API
            
            logger.info(f"Order completed: {order_id} for {customer_email}")
            
        elif event_type == 'order.refunded':
            # Handle refund - invalidate code if needed
            order_id = data.get('order_id')
            logger.info(f"Order refunded: {order_id}")
        
        return create_response(True, "Webhook processed")
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return create_response(False, str(e)), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Sellauth Integration on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
