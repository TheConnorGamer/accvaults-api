# AccVaults Sellauth Integration

A Flask web application that provides the same SMB Panel functionality as the Discord bot, designed for integration with Sellauth or any e-commerce platform.

## Features

✅ **Code Redemption System**
- Validate and redeem codes purchased through Sellauth
- Automatic order creation on SMB Panel
- Link validation for different platforms
- Support for refillable services

✅ **REST API Endpoints**
- `/api/services` - Browse all available services
- `/api/search` - Search services with filters
- `/api/redeem` - Redeem codes and create orders
- `/api/validate-code` - Validate codes before redemption
- `/api/user/redemptions` - Get user redemption history

✅ **Admin Endpoints** (Require API Key)
- `/api/admin/balance` - Check SMB Panel balance
- `/api/admin/order` - Create orders directly
- `/api/admin/codes` - Manage redemption codes
- `/api/admin/redemptions` - View all redemptions

✅ **Sellauth Integration**
- Webhook support for automatic code delivery
- Signature verification for security
- Order completion and refund handling

✅ **Beautiful Web UI**
- Modern, responsive design
- Real-time validation
- Animated success screens
- Mobile-friendly interface

## Installation

### 1. Install Dependencies

```bash
cd For-Sellauth
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit `config/.env` and set your configuration:

```env
# SMB Panel API Key (required)
SMBPANEL_API_KEY=your-api-key-here

# Flask Secret Key (required for sessions)
FLASK_SECRET_KEY=your-random-secret-key

# Sellauth Configuration
SELLAUTH_WEBHOOK_SECRET=your-webhook-secret
SELLAUTH_API_KEY=your-sellauth-api-key

# Admin API Key (for admin endpoints)
ADMIN_API_KEY=your-secure-admin-key
```

### 3. Run the Application

**Development:**
```bash
python app.py
```

**Production (with Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

The application will be available at `http://localhost:5000`

## Usage

### Web Interface

1. Navigate to `http://localhost:5000`
2. Enter your redemption code
3. Click "Validate Code" to verify
4. Enter the link where you want the service delivered
5. Click "Redeem Now" to complete

### API Usage

#### Validate a Code

```bash
curl -X POST http://localhost:5000/api/validate-code \
  -H "Content-Type: application/json" \
  -d '{"code": "XXXX-XXXX-XXXX-XXXX"}'
```

#### Redeem a Code

```bash
curl -X POST http://localhost:5000/api/redeem \
  -H "Content-Type: application/json" \
  -d '{
    "code": "XXXX-XXXX-XXXX-XXXX",
    "link": "https://youtube.com/@username",
    "user_id": "customer123",
    "username": "John Doe"
  }'
```

#### Search Services

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "youtube subscribers",
    "max_price": 5.00,
    "refill_only": true
  }'
```

#### Admin - Check Balance

```bash
curl -X GET http://localhost:5000/api/admin/balance \
  -H "X-API-Key: your-admin-api-key"
```

#### Admin - Get All Codes

```bash
curl -X GET http://localhost:5000/api/admin/codes?status=unused \
  -H "X-API-Key: your-admin-api-key"
```

## Sellauth Integration

### Setting Up Webhooks

1. Log into your Sellauth dashboard
2. Go to Settings → Webhooks
3. Add a new webhook with URL: `https://yourdomain.com/webhook/sellauth`
4. Select events: `order.completed`, `order.refunded`
5. Copy the webhook secret to your `.env` file

### Webhook Events

**Order Completed:**
- Triggered when a customer completes a purchase
- Use this to automatically deliver codes to customers
- Access customer email and order details

**Order Refunded:**
- Triggered when an order is refunded
- Use this to invalidate redeemed codes if needed

### Example Webhook Handler

The webhook endpoint at `/webhook/sellauth` handles:
- Signature verification for security
- Order completion events
- Refund events
- Automatic code assignment (customize as needed)

## Code Generation

Use the existing code generator from the parent directory:

```bash
cd ..
python src/generate_codes.py
```

Or use the GUI:
```bash
AccVaults_Code_Generator.exe
```

## Deployment

### Deploy to VPS/Server

1. Install dependencies:
```bash
sudo apt update
sudo apt install python3 python3-pip nginx
```

2. Clone your project and install requirements:
```bash
cd /var/www/sellauth-integration
pip3 install -r requirements.txt
```

3. Set up Gunicorn service:
```bash
sudo nano /etc/systemd/system/sellauth.service
```

```ini
[Unit]
Description=Sellauth Integration
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/sellauth-integration
Environment="PATH=/usr/local/bin"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

4. Configure Nginx:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. Start services:
```bash
sudo systemctl start sellauth
sudo systemctl enable sellauth
sudo systemctl restart nginx
```

### Deploy to Heroku

1. Create `Procfile`:
```
web: gunicorn app:app
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
heroku config:set SMBPANEL_API_KEY=your-key
```

## Security

- ✅ Webhook signature verification
- ✅ Admin API key authentication
- ✅ CORS protection
- ✅ Input validation
- ✅ SQL injection prevention (parameterized queries)
- ✅ Rate limiting (configurable)

## File Structure

```
For-Sellauth/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── config/
│   └── .env              # Configuration file
├── templates/
│   └── index.html        # Web UI
└── README.md             # This file
```

## API Response Format

All API endpoints return JSON in this format:

```json
{
  "success": true,
  "message": "Operation successful",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    // Response data here
  }
}
```

## Support

For issues or questions:
- Check the logs for error messages
- Verify your API keys are correct
- Ensure the database path is accessible
- Test endpoints with curl or Postman

## License

Same as parent project - AccVaults SMB Panel Bot
