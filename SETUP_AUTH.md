# Cargo Authentication System - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and set:
- `ADMIN_EMAIL`: Your admin email (dmtoravi@gmail.com recommended)
- `ADMIN_PASSWORD`: Strong password (min 8 chars, uppercase, digit)
- `FLASK_SECRET_KEY`: Run `python -c "import secrets; print(secrets.token_hex(32))"` to generate

### 3. Initialize Database

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized')"
```

### 4. Create Admin Account

Set environment variable and run:

```bash
export ADMIN_PASSWORD="YourSecurePassword123"
python scripts/init_admin.py
```

Or create manually in Python:

```python
from app import app, db
from services.models import User
from services.auth_service import AuthService

with app.app_context():
    admin = User(
        email='dmtoravi@gmail.com',
        full_name='Administrator',
        password_hash=AuthService.hash_password('YourSecurePassword123'),
        account_status='approved',
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin created!")
```

### 5. Start Application

```bash
python app.py
```

Visit: `http://localhost:5000`

## First Login

1. Go to `/login`
2. Enter admin email and password
3. Click "Admin" button in top navbar
4. Visit `/admin` to manage users

## User Registration Flow

1. New user visits `/register`
2. Creates account (status: `pending`)
3. Sees "Awaiting approval" message
4. Admin approves in `/admin` dashboard
5. User logs in and can use Cargo

## Admin Dashboard Features

- **Overview**: User statistics and counts
- **User Management**: Approve, reject, revoke, suspend, restore users
- **Audit Log**: View all administrative actions
- **Search & Filter**: Find users by email/name and status

## Key Files

- `app.py` - Flask application with auth routes
- `services/models.py` - Database models
- `services/auth_service.py` - Authentication logic
- `services/admin_service.py` - Admin operations
- `services/decorators.py` - Auth decorators
- `templates/login.html` - Login page
- `templates/register.html` - Registration page
- `templates/admin.html` - Admin dashboard
- `static/js/admin.js` - Admin dashboard logic

## Important Notes

### Security

- All passwords hashed with bcrypt
- Sessions stored server-side (15 min timeout)
- Every request validates user status
- Revocation immediately invalidates all sessions
- All admin actions logged

### Environment Variables

Required:
- `ADMIN_EMAIL` - Initial admin email
- `ADMIN_PASSWORD` - Initial admin password (for setup only)

Optional:
- `FLASK_SECRET_KEY` - Flask secret (auto-generated if not set)
- `DATABASE_URL` - Database URI (default: sqlite:///cargo.db)
- `SESSION_TIMEOUT` - Session timeout in seconds (default: 900)
- `FLASK_DEBUG` - Debug mode (default: False)

### Database

- SQLite by default: `cargo.db`
- For production, use PostgreSQL or MySQL
- Tables: `users`, `sessions`, `audit_logs`

## Existing Features Preserved

✅ Airline name replacement  
✅ Emoji and Unicode support  
✅ PDF generation (single & bulk)  
✅ Copy-ready posts  
✅ Template management  
✅ Dark mode  
✅ CSV/TXT import  
✅ All original UI and branding  

## Troubleshooting

**Module not found errors?**
```bash
pip install -r requirements.txt
```

**Database errors?**
```bash
rm cargo.db
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

**Admin password wrong?**

Create new admin:
```python
from app import app, db
from services.models import User
from services.auth_service import AuthService

with app.app_context():
    user = User.query.filter_by(email='dmtoravi@gmail.com').first()
    if user:
        user.password_hash = AuthService.hash_password('NewPassword123')
        db.session.commit()
        print("Password updated!")
```

**Cannot access admin dashboard?**

Verify admin flag:
```python
from app import app, db
from services.models import User

with app.app_context():
    user = User.query.filter_by(email='dmtoravi@gmail.com').first()
    print(f"User: {user.email}, Admin: {user.is_admin}, Status: {user.account_status}")
```

## Production Deployment

**Before deploying:**

1. Set strong `FLASK_SECRET_KEY`
2. Set `FLASK_DEBUG=False`
3. Use HTTPS with secure cookies
4. Switch to PostgreSQL or MySQL
5. Store `.env` securely (not in git)
6. Use Gunicorn or uWSGI

**Example with Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Full Documentation

See `AUTHENTICATION.md` for complete documentation on:
- Database schema
- API endpoints
- Security considerations
- Testing procedures
- Troubleshooting guide

---

**Ready to go!** Follow the Quick Start steps above, then visit http://localhost:5000
