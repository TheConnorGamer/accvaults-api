# Sellauth Integration Guide

Complete guide for integrating AccVaults with your Sellauth store.

## Table of Contents
1. [Overview](#overview)
2. [Setting Up Your Server](#setting-up-your-server)
3. [Configuring Sellauth](#configuring-sellauth)
4. [Webhook Integration](#webhook-integration)
5. [Product Setup](#product-setup)
6. [Code Delivery](#code-delivery)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Overview

This integration allows you to:
- Sell SMM services through Sellauth
- Automatically deliver redemption codes to customers
- Track orders and redemptions
- Manage inventory through admin dashboard

## Setting Up Your Server

### 1. Install the Application

```bash
cd For-Sellauth
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit `config/.env`:

```env
# Required
SMBPANEL_API_KEY=your-smb-panel-api-key
FLASK_SECRET_KEY=generate-random-secret-key
ADMIN_API_KEY=create-secure-admin-key

# Sellauth (get from Sellauth dashboard)
SELLAUTH_WEBHOOK_SECRET=your-webhook-secret
SELLAUTH_API_KEY=your-sellauth-api-key

# Optional
PORT=5000
FLASK_DEBUG=False
```

### 3. Deploy to Production

**Option A: VPS/Dedicated Server**

1. Install dependencies:
```bash
sudo apt update
sudo apt install python3 python3-pip nginx certbot python3-certbot-nginx
```

2. Set up the application:
```bash
sudo mkdir -p /var/www/accvaults
sudo cp -r For-Sellauth/* /var/www/accvaults/
cd /var/www/accvaults
pip3 install -r requirements.txt
```

3. Create systemd service:
```bash
sudo nano /etc/systemd/system/accvaults.service
```

```ini
[Unit]
Description=AccVaults Sellauth Integration
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/accvaults
Environment="PATH=/usr/local/bin"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

4. Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/accvaults
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

5. Enable and start:
```bash
sudo ln -s /etc/nginx/sites-available/accvaults /etc/nginx/sites-enabled/
sudo systemctl start accvaults
sudo systemctl enable accvaults
sudo systemctl restart nginx
```

6. Get SSL certificate:
```bash
sudo certbot --nginx -d yourdomain.com
```

**Option B: Heroku**

1. Create `Procfile` (already included):
```
web: gunicorn app:app
```

2. Deploy:
```bash
heroku create your-app-name
git add .
git commit -m "Initial commit"
git push heroku main
heroku config:set SMBPANEL_API_KEY=your-key
heroku config:set FLASK_SECRET_KEY=your-secret
heroku config:set ADMIN_API_KEY=your-admin-key
```

**Option C: Railway/Render**

Similar to Heroku - just connect your Git repo and set environment variables.

## Configuring Sellauth

### 1. Create Products

1. Log into your Sellauth dashboard
2. Go to **Products** → **Create Product**
3. Set up your product:
   - **Name**: "1000 YouTube Subscribers" (example)
   - **Price**: Your selling price
   - **Type**: Digital Product
   - **Delivery**: Automatic (via webhook)
   - **Stock**: Set based on available codes

### 2. Set Up Webhooks

1. Go to **Settings** → **Webhooks**
2. Click **Add Webhook**
3. Configure:
   - **URL**: `https://yourdomain.com/webhook/sellauth`
   - **Events**: Select:
     - ✅ `order.completed`
     - ✅ `order.refunded`
   - **Secret**: Copy this - you'll need it for `.env`

4. Save and copy the webhook secret to your `.env` file

### 3. Get API Key

1. Go to **Settings** → **API**
2. Generate new API key
3. Copy to `.env` file as `SELLAUTH_API_KEY`

## Webhook Integration

### Understanding Webhook Events

**order.completed**
- Triggered when customer completes payment
- Use this to deliver redemption codes
- Contains customer email and order details

**order.refunded**
- Triggered when order is refunded
- Use this to invalidate codes (optional)

### Implementing Code Delivery

Edit `app.py` webhook handler to deliver codes:

```python
@app.route('/webhook/sellauth', methods=['POST'])
def sellauth_webhook():
    try:
        # Verify signature
        signature = request.headers.get('X-Sellauth-Signature', '')
        payload = request.get_data(as_text=True)
        
        if not verify_sellauth_webhook(payload, signature):
            return create_response(False, "Invalid signature"), 401
        
        data = request.get_json()
        event_type = data.get('event')
        
        if event_type == 'order.completed':
            customer_email = data.get('customer', {}).get('email')
            product_id = data.get('product', {}).get('id')
            order_id = data.get('order_id')
            
            # Get an unused code for this product
            # Map product_id to service type
            product_mapping = {
                'prod_123': {'platform': 'youtube', 'service_type': 'subscribers'},
                'prod_456': {'platform': 'instagram', 'service_type': 'followers'},
                # Add your product mappings
            }
            
            if product_id in product_mapping:
                service_info = product_mapping[product_id]
                
                # Get unused code from database
                codes = redeem_db.get_all_codes(status='unused')
                matching_codes = [c for c in codes 
                                if c['platform'] == service_info['platform'] 
                                and c['service_type'] == service_info['service_type']]
                
                if matching_codes:
                    code = matching_codes[0]['code']
                    
                    # Send code to customer via Sellauth API
                    send_code_to_customer(customer_email, code, order_id)
                    
                    logger.info(f"Delivered code {code} to {customer_email}")
                else:
                    logger.error(f"No codes available for product {product_id}")
                    # Alert admin - out of stock
            
        return create_response(True, "Webhook processed")
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return create_response(False, str(e)), 500

def send_code_to_customer(email, code, order_id):
    """Send redemption code to customer via Sellauth API"""
    import requests
    
    sellauth_api_key = os.getenv('SELLAUTH_API_KEY')
    
    # Construct redemption URL
    redemption_url = f"https://yourdomain.com/?code={code}"
    
    # Email content
    message = f"""
    Thank you for your purchase!
    
    Your redemption code: {code}
    
    To redeem:
    1. Visit: {redemption_url}
    2. Enter your code
    3. Provide the link where you want the service delivered
    
    Need help? Contact support@yourdomain.com
    """
    
    # Send via Sellauth API (adjust based on Sellauth's API docs)
    response = requests.post(
        'https://api.sellauth.com/v1/orders/deliver',
        headers={'Authorization': f'Bearer {sellauth_api_key}'},
        json={
            'order_id': order_id,
            'message': message
        }
    )
    
    return response.json()
```

## Product Setup

### Creating Product Mappings

Create a mapping file to link Sellauth products to your services:

```python
# product_mappings.py
PRODUCT_MAPPINGS = {
    # YouTube Services
    'prod_yt_subs_1k': {
        'platform': 'youtube',
        'service_type': 'subscribers',
        'quantity': 1000,
        'service_id': 22662  # Your SMB Panel service ID
    },
    'prod_yt_views_10k': {
        'platform': 'youtube',
        'service_type': 'views',
        'quantity': 10000,
        'service_id': 12345
    },
    
    # Instagram Services
    'prod_ig_followers_1k': {
        'platform': 'instagram',
        'service_type': 'followers',
        'quantity': 1000,
        'service_id': 54321
    },
    
    # Add more products...
}
```

### Generating Codes for Products

Use the code generator to create codes for each product:

```bash
# Generate 100 codes for YouTube Subscribers
python ../src/generate_codes.py 100 22662 1000 youtube subscribers YT

# Generate 50 codes for Instagram Followers
python ../src/generate_codes.py 50 54321 1000 instagram followers IG
```

## Code Delivery

### Method 1: Email Delivery (Recommended)

Codes are automatically emailed to customers after purchase using Sellauth's delivery system.

### Method 2: Dashboard Delivery

Customers can view their codes in the Sellauth customer dashboard.

### Method 3: Direct Link

Provide a direct redemption link: `https://yourdomain.com/?code=XXXX-XXXX-XXXX-XXXX`

## Testing

### 1. Test Webhook Locally

Use ngrok for local testing:

```bash
ngrok http 5000
```

Update Sellauth webhook URL to: `https://your-ngrok-url.ngrok.io/webhook/sellauth`

### 2. Test Code Redemption

1. Visit `http://localhost:5000`
2. Enter a test code
3. Validate and redeem
4. Check admin dashboard for redemption

### 3. Test Webhook

Create a test order in Sellauth and verify:
- Webhook is received
- Code is delivered to customer
- Order appears in admin dashboard

## Troubleshooting

### Webhook Not Receiving Events

1. Check webhook URL is correct and accessible
2. Verify webhook secret matches `.env`
3. Check server logs: `tail -f /var/log/accvaults.log`
4. Test webhook manually with curl:

```bash
curl -X POST https://yourdomain.com/webhook/sellauth \
  -H "Content-Type: application/json" \
  -H "X-Sellauth-Signature: test" \
  -d '{"event": "order.completed", "order_id": "test123"}'
```

### Codes Not Being Delivered

1. Check product mapping exists
2. Verify unused codes are available
3. Check Sellauth API key is valid
4. Review application logs

### Invalid Signature Error

1. Verify webhook secret in `.env` matches Sellauth
2. Check signature verification logic
3. Ensure payload is not modified

### Out of Stock

1. Generate more codes using code generator
2. Set up low stock alerts
3. Monitor admin dashboard regularly

## Best Practices

1. **Security**
   - Keep API keys secret
   - Use HTTPS in production
   - Verify webhook signatures
   - Implement rate limiting

2. **Inventory Management**
   - Monitor code stock regularly
   - Set up alerts for low inventory
   - Generate codes in batches
   - Track redemption rates

3. **Customer Experience**
   - Provide clear redemption instructions
   - Include support contact
   - Set realistic delivery expectations
   - Test the full customer journey

4. **Monitoring**
   - Check logs regularly
   - Monitor webhook delivery
   - Track redemption success rate
   - Set up error notifications

## Support

For issues:
1. Check application logs
2. Review Sellauth webhook logs
3. Test endpoints with Postman/curl
4. Verify all configuration values

## Additional Resources

- [Sellauth API Documentation](https://docs.sellauth.com)
- [SMB Panel API Documentation](https://smbpanel.net/api)
- [Flask Documentation](https://flask.palletsprojects.com)
