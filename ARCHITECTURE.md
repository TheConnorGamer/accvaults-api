# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SELLAUTH PLATFORM                        │
│  (Customer purchases product → Triggers webhook)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Webhook Event
                             │ (order.completed)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FOR-SELLAUTH WEB APP                          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Flask App  │  │  REST API    │  │  Web UI      │          │
│  │   (app.py)   │  │  Endpoints   │  │  (HTML/JS)   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│         └─────────────────┴──────────────────┘                   │
│                           │                                       │
│         ┌─────────────────┴─────────────────┐                   │
│         │                                     │                   │
│         ▼                                     ▼                   │
│  ┌──────────────┐                    ┌──────────────┐           │
│  │  SMB Panel   │                    │  Redeem DB   │           │
│  │  API Client  │                    │  (SQLite)    │           │
│  │ (smb_panel)  │                    │ (redeem_db)  │           │
│  └──────┬───────┘                    └──────┬───────┘           │
│         │                                     │                   │
└─────────┼─────────────────────────────────────┼──────────────────┘
          │                                     │
          │                                     │
          ▼                                     ▼
┌─────────────────┐                   ┌─────────────────┐
│   SMB PANEL     │                   │  Database File  │
│   API Server    │                   │  redeem_codes.db│
│ (smbpanel.net)  │                   │  (Shared with   │
│                 │                   │  Discord Bot)   │
└─────────────────┘                   └─────────────────┘
```

## Request Flow

### 1. Code Redemption Flow

```
Customer
   │
   │ 1. Visits redemption page
   ▼
┌─────────────────┐
│  Web Browser    │
│  (index.html)   │
└────────┬────────┘
         │
         │ 2. Enters code
         │ POST /api/validate-code
         ▼
┌─────────────────┐
│   Flask App     │
│   (app.py)      │
└────────┬────────┘
         │
         │ 3. Check code validity
         ▼
┌─────────────────┐
│  Redeem DB      │
│  is_code_valid()│
└────────┬────────┘
         │
         │ 4. Return code details
         ▼
┌─────────────────┐
│  Web Browser    │
│  Shows service  │
│  details        │
└────────┬────────┘
         │
         │ 5. User enters link
         │ POST /api/redeem
         ▼
┌─────────────────┐
│   Flask App     │
│   Validates link│
└────────┬────────┘
         │
         │ 6. Create order
         ▼
┌─────────────────┐
│  SMB Panel API  │
│  create_order() │
└────────┬────────┘
         │
         │ 7. Order ID returned
         ▼
┌─────────────────┐
│  Redeem DB      │
│  mark_code_used()│
│  add_history()  │
└────────┬────────┘
         │
         │ 8. Success response
         ▼
┌─────────────────┐
│  Web Browser    │
│  Shows success  │
└─────────────────┘
```

### 2. Sellauth Webhook Flow

```
Sellauth
   │
   │ Customer completes purchase
   │
   │ POST /webhook/sellauth
   │ + Signature header
   ▼
┌─────────────────┐
│   Flask App     │
│   Webhook       │
│   Handler       │
└────────┬────────┘
         │
         │ 1. Verify signature
         ▼
┌─────────────────┐
│  HMAC Verify    │
│  (Security)     │
└────────┬────────┘
         │
         │ 2. Parse event data
         ▼
┌─────────────────┐
│  Event Handler  │
│  (order.        │
│   completed)    │
└────────┬────────┘
         │
         │ 3. Get unused code
         ▼
┌─────────────────┐
│  Redeem DB      │
│  get_all_codes()│
│  (status=unused)│
└────────┬────────┘
         │
         │ 4. Send to customer
         ▼
┌─────────────────┐
│  Sellauth API   │
│  or Email       │
│  Service        │
└─────────────────┘
```

### 3. Admin Dashboard Flow

```
Admin
   │
   │ 1. Visits /admin
   ▼
┌─────────────────┐
│  Login Modal    │
│  (admin.html)   │
└────────┬────────┘
         │
         │ 2. Enters API key
         │ GET /api/admin/balance
         │ Header: X-API-Key
         ▼
┌─────────────────┐
│   Flask App     │
│   verify_admin_ │
│   key()         │
└────────┬────────┘
         │
         │ 3. If valid, load data
         ▼
┌─────────────────────────────────┐
│  Multiple API calls:            │
│  - GET /api/admin/balance       │
│  - GET /api/admin/codes         │
│  - GET /api/admin/redemptions   │
└────────┬────────────────────────┘
         │
         │ 4. Display dashboard
         ▼
┌─────────────────┐
│  Admin UI       │
│  - Stats cards  │
│  - Tables       │
│  - Charts       │
└─────────────────┘
```

## Component Details

### Flask App (app.py)

**Responsibilities:**
- HTTP request handling
- Route management
- Authentication/authorization
- Response formatting
- Error handling

**Key Functions:**
- `verify_sellauth_webhook()` - Webhook security
- `verify_admin_key()` - Admin authentication
- `create_response()` - Standardized JSON responses

### SMB Panel Client (smb_panel.py)

**Responsibilities:**
- API communication with SMB Panel
- Request formatting
- Response parsing
- Error handling

**Methods:**
- `get_balance()` - Account balance
- `get_services()` - Service catalog
- `create_order()` - Place orders
- `get_order_status()` - Track orders
- `refill_order()` - Request refills

### Redeem Database (redeem_db.py)

**Responsibilities:**
- Code storage and retrieval
- Code validation
- Redemption tracking
- History management

**Methods:**
- `add_code()` - Create new code
- `get_code()` - Retrieve code details
- `is_code_valid()` - Validate code
- `mark_code_used()` - Mark as redeemed
- `add_redemption_history()` - Log redemption
- `get_user_redemptions()` - User history

### Link Validator (link_validator.py)

**Responsibilities:**
- Platform-specific URL validation
- Service type matching
- Error messaging

**Validation Rules:**
- YouTube subscribers → Channel URL
- YouTube views → Video URL
- Instagram followers → Profile URL
- Instagram likes → Post URL
- TikTok followers → Profile URL
- And more...

## Database Schema

### codes Table

```sql
CREATE TABLE codes (
    code TEXT PRIMARY KEY,
    service_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    platform TEXT NOT NULL,
    service_type TEXT NOT NULL,
    requirements TEXT,
    status TEXT DEFAULT 'unused',
    created_date TEXT NOT NULL,
    used_date TEXT,
    used_by_user_id TEXT,
    order_id INTEGER,
    expiry_days INTEGER DEFAULT 30,
    has_refill INTEGER DEFAULT 0
)
```

### redemption_history Table

```sql
CREATE TABLE redemption_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    service_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    link TEXT NOT NULL,
    order_id INTEGER,
    redeemed_date TEXT NOT NULL,
    FOREIGN KEY (code) REFERENCES codes(code)
)
```

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Redemption page | No |
| GET | `/admin` | Admin dashboard | No (API key in UI) |
| GET | `/api/health` | Health check | No |
| GET | `/api/services` | List services | No |
| POST | `/api/search` | Search services | No |
| POST | `/api/validate-code` | Validate code | No |
| POST | `/api/redeem` | Redeem code | No |
| POST | `/api/user/redemptions` | User history | No |

### Admin Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/balance` | SMB balance | X-API-Key |
| POST | `/api/admin/order` | Create order | X-API-Key |
| GET | `/api/admin/codes` | List codes | X-API-Key |
| GET | `/api/admin/redemptions` | List redemptions | X-API-Key |

### Webhook Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/webhook/sellauth` | Sellauth events | Signature |

## Security Layers

```
┌─────────────────────────────────────────┐
│  1. HTTPS/SSL Encryption                │
│     (Transport Layer Security)          │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  2. CORS Protection                     │
│     (Cross-Origin Resource Sharing)     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  3. Webhook Signature Verification      │
│     (HMAC-SHA256)                       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  4. Admin API Key Authentication        │
│     (Header-based)                      │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  5. Input Validation                    │
│     (Link validation, code format)      │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  6. SQL Injection Prevention            │
│     (Parameterized queries)             │
└─────────────────────────────────────────┘
```

## Deployment Architecture

### Production Setup

```
Internet
   │
   │ HTTPS (443)
   ▼
┌─────────────────┐
│  Nginx/Apache   │  ← Reverse Proxy
│  (Web Server)   │  ← SSL Termination
└────────┬────────┘  ← Static Files
         │
         │ HTTP (5000)
         ▼
┌─────────────────┐
│  Gunicorn       │  ← WSGI Server
│  (4 workers)    │  ← Process Manager
└────────┬────────┘
         │
         │
         ▼
┌─────────────────┐
│  Flask App      │  ← Application
│  (app.py)       │  ← Business Logic
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  SMB Panel  │  │  Database   │  │  Sellauth   │
│  API        │  │  (SQLite)   │  │  API        │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Scalability Considerations

### Horizontal Scaling

```
Load Balancer
      │
      ├─────────┬─────────┬─────────┐
      │         │         │         │
      ▼         ▼         ▼         ▼
   App 1     App 2     App 3     App 4
      │         │         │         │
      └─────────┴─────────┴─────────┘
                  │
                  ▼
          Shared Database
```

**Note:** Current SQLite database is suitable for single-instance deployment. For horizontal scaling, migrate to PostgreSQL or MySQL.

### Caching Strategy

```
Request
   │
   ▼
┌─────────────┐
│  Redis      │  ← Cache services list
│  Cache      │  ← Cache balance (TTL: 60s)
└─────┬───────┘  ← Cache user sessions
      │
      │ Cache miss
      ▼
┌─────────────┐
│  Database   │
│  or API     │
└─────────────┘
```

## Monitoring & Logging

```
Application
   │
   ├─── Logs ────────────────┐
   │                         │
   ▼                         ▼
┌─────────────┐    ┌─────────────┐
│  File Logs  │    │  Syslog     │
│  app.log    │    │  (Optional) │
└─────────────┘    └─────────────┘
   │
   │ (Optional)
   ▼
┌─────────────┐
│  Log        │
│  Aggregator │
│  (ELK/etc)  │
└─────────────┘
```

## File Structure

```
For-Sellauth/
│
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── Procfile                        # Heroku deployment
├── START_SERVER.bat                # Windows quick start
├── .gitignore                      # Git ignore rules
│
├── config/
│   └── .env                        # Configuration file
│
├── templates/
│   ├── index.html                  # Public redemption page
│   └── admin.html                  # Admin dashboard
│
└── docs/
    ├── README.md                   # Main documentation
    ├── QUICK_START.md              # Quick start guide
    ├── SELLAUTH_INTEGRATION_GUIDE.md  # Sellauth setup
    ├── FEATURES_COMPARISON.md      # Bot vs Web comparison
    └── ARCHITECTURE.md             # This file
```

## Technology Stack

**Backend:**
- Python 3.8+
- Flask 3.0.0 (Web framework)
- Flask-CORS (Cross-origin support)
- python-dotenv (Environment variables)
- requests (HTTP client)
- Gunicorn (WSGI server)

**Frontend:**
- HTML5
- Tailwind CSS (Styling)
- Vanilla JavaScript (Interactivity)
- Font Awesome (Icons)

**Database:**
- SQLite3 (Embedded database)

**External APIs:**
- SMB Panel API (Service provider)
- Sellauth API (E-commerce platform)

## Performance Metrics

**Expected Performance:**
- API Response Time: <100ms
- Code Validation: <50ms
- Order Creation: <2s (depends on SMB Panel)
- Concurrent Users: 100+ (single instance)
- Database Queries: <10ms

**Resource Usage:**
- RAM: ~100-200MB per worker
- CPU: Minimal (<5% idle)
- Disk: <1MB (excluding database)
- Bandwidth: ~1KB per request

## Future Enhancements

Potential improvements:
1. PostgreSQL/MySQL support for scaling
2. Redis caching layer
3. Rate limiting per IP
4. Email notifications
5. SMS code delivery
6. Multi-language support
7. Analytics dashboard
8. Automated stock alerts
9. Bulk code generation UI
10. Customer portal with order history
