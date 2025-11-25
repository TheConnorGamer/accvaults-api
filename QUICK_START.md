# Quick Start Guide

Get your Sellauth integration running in 5 minutes!

## Prerequisites

- Python 3.8 or higher
- SMB Panel API key
- (Optional) Sellauth account for webhook integration

## Step 1: Install Dependencies

```bash
cd For-Sellauth
pip install -r requirements.txt
```

## Step 2: Configure

Edit `config/.env`:

```env
# Required - Get from SMB Panel
SMBPANEL_API_KEY=your-api-key-here

# Required - Generate a random string
FLASK_SECRET_KEY=your-random-secret-key

# Required - Create a secure admin password
ADMIN_API_KEY=your-admin-password
```

## Step 3: Generate Some Test Codes

```bash
# Go back to parent directory
cd ..

# Generate 5 test codes for YouTube subscribers
python src/generate_codes.py 5 22662 1000 youtube subscribers TEST
```

This creates 5 codes in the database that you can use for testing.

## Step 4: Start the Server

```bash
cd For-Sellauth
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

## Step 5: Test It Out!

### Test the Web Interface

1. Open browser: `http://localhost:5000`
2. Enter one of your test codes (format: `TEST-XXXX-XXXX-XXXX-XXXX`)
3. Click "Validate Code"
4. Enter a YouTube channel URL (e.g., `https://youtube.com/@username`)
5. Click "Redeem Now"

### Test the Admin Dashboard

1. Open browser: `http://localhost:5000/admin`
2. Enter your `ADMIN_API_KEY` from `.env`
3. View stats, codes, and redemptions

### Test the API

**Validate a code:**
```bash
curl -X POST http://localhost:5000/api/validate-code \
  -H "Content-Type: application/json" \
  -d '{"code": "TEST-XXXX-XXXX-XXXX-XXXX"}'
```

**Get all services:**
```bash
curl http://localhost:5000/api/services
```

**Search services:**
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "youtube subscribers", "max_price": 5.00}'
```

## What's Next?

### For Local Development
- Keep using `python app.py` for testing
- Access at `http://localhost:5000`
- Check logs in terminal

### For Production Deployment
- See [README.md](README.md) for deployment options
- See [SELLAUTH_INTEGRATION_GUIDE.md](SELLAUTH_INTEGRATION_GUIDE.md) for Sellauth setup

### For Sellauth Integration
1. Deploy to a server with public URL
2. Set up webhook in Sellauth dashboard
3. Configure product mappings
4. Test with real orders

## Common Issues

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "Database not found" error
The app will create the database automatically. Make sure the parent `data/` folder exists:
```bash
mkdir -p ../data
```

### "Invalid API key" error
Check that `SMBPANEL_API_KEY` in `.env` is correct.

### Port already in use
Change the port in `.env`:
```env
PORT=8000
```

## File Structure

```
For-Sellauth/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── config/
│   └── .env                       # Configuration (edit this!)
├── templates/
│   ├── index.html                 # Public redemption page
│   └── admin.html                 # Admin dashboard
├── README.md                       # Full documentation
├── SELLAUTH_INTEGRATION_GUIDE.md  # Sellauth setup guide
└── QUICK_START.md                 # This file
```

## API Endpoints Reference

### Public Endpoints
- `GET /` - Redemption page
- `GET /admin` - Admin dashboard
- `GET /api/health` - Health check
- `GET /api/services` - List all services
- `POST /api/search` - Search services
- `POST /api/validate-code` - Validate a code
- `POST /api/redeem` - Redeem a code
- `POST /api/user/redemptions` - Get user's redemptions

### Admin Endpoints (Require `X-API-Key` header)
- `GET /api/admin/balance` - SMB Panel balance
- `POST /api/admin/order` - Create order directly
- `GET /api/admin/codes` - List all codes
- `GET /api/admin/redemptions` - List all redemptions

### Webhook Endpoint
- `POST /webhook/sellauth` - Sellauth webhook handler

## Need Help?

1. Check the logs in your terminal
2. Read the full [README.md](README.md)
3. Review [SELLAUTH_INTEGRATION_GUIDE.md](SELLAUTH_INTEGRATION_GUIDE.md)
4. Test API endpoints with curl or Postman

## Security Notes

⚠️ **Important for Production:**
- Change `FLASK_SECRET_KEY` to a random string
- Use a strong `ADMIN_API_KEY`
- Set `FLASK_DEBUG=False`
- Use HTTPS (SSL certificate)
- Keep `.env` file private (never commit to Git)

## Example .env for Production

```env
SMBPANEL_API_KEY=your-real-api-key
FLASK_SECRET_KEY=use-a-random-64-character-string-here
ADMIN_API_KEY=use-a-strong-password-here
FLASK_DEBUG=False
PORT=5000
SELLAUTH_WEBHOOK_SECRET=get-from-sellauth-dashboard
SELLAUTH_API_KEY=get-from-sellauth-dashboard
LOG_LEVEL=INFO
```

---

**You're all set! 🎉**

Your Sellauth integration is now running. Test it out and customize as needed!
