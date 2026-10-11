# Cargo Authentication & Admin System

## Overview

Cargo now includes a complete authentication system with admin-controlled user approval, revocable access, and audit logging. All users must register and be approved by an administrator before accessing the application.

## Features

### User Management
- **Registration**: Users create accounts with email, name, and password
- **Account Status**: Pending → Approved → Active (or Rejected/Revoked/Suspended)
- **Password Security**: Passwords hashed with bcrypt (werkzeug.security)
- **Session Management**: Short-lived sessions (15 min) with server-side invalidation

### Admin Controls
- **User Approval**: Approve pending registrations
- **Account Rejection**: Reject registrations with optional reason
- **Access Revocation**: Immediately revoke user access and invalidate sessions
- **Account Suspension**: Temporarily disable accounts
- **Audit Logging**: Track all administrative actions with timestamps

### Security
- All protected routes require authentication (`@auth_required` decorator)
- Admin routes require admin privileges (`@admin_required` decorator)
- Sessions stored server-side and validated on every request
- Rate limiting on login (5 attempts per minute)
- Input validation on all forms (server-side)
- XSS prevention via template auto-escaping
- SQL injection prevention via SQLAlchemy ORM

## Setup & Deployment

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Admin account
ADMIN_EMAIL=dmtoravi@gmail.com
ADMIN_PASSWORD=YourSecureAdminPassword123

# Flask
FLASK_SECRET_KEY=generate-a-random-key-here

# Database (SQLite by default)
DATABASE_URL=sqlite:///cargo.db

# Sessions
SESSION_TIMEOUT=900          # 15 minutes
REFRESH_TOKEN_EXPIRY=604800  # 7 days
```

**Important**: Generate a strong random key for `FLASK_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Initialize Database

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 4. Create Admin Account

```bash
export ADMIN_PASSWORD="your-secure-password"
python scripts/init_admin.py
```

Or use the Python REPL:

```python
from app import app, db
from services.models import User
from services.auth_service import AuthService

with app.app_context():
    admin = User(
        email='dmtoravi@gmail.com',
        full_name='Administrator',
        password_hash=AuthService.hash_password('your-secure-password'),
        account_status='approved',
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin account created")
```

### 5. Start the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## User Workflows

### Registration & Approval

1. **User Registration**: Visit `/register`
   - Enter email, full name, password
   - Account created with `pending` status
   - Shows "Awaiting approval" message

2. **Admin Approval**: Visit `/admin`
   - View pending users
   - Click "Approve" to grant access
   - User receives approved status

3. **User Login**: Visit `/login`
   - Enter approved email and password
   - Session created
   - Redirected to Cargo application

### Access Revocation

1. **Admin Revokes Access**: Visit `/admin`
   - Click "Revoke" on an approved user
   - User status changes to `revoked`
   - All user sessions immediately invalidated

2. **Revoked User Actions**:
   - Next API request returns 401 (Unauthorized)
   - Redirected to `/revoked` page
   - Cannot use Cargo until access is restored

### Account Status Transitions

```
Pending ──→ Approved ──→ Revoked ──→ Restored ──→ Approved
     └──→ Rejected
     
Approved ──→ Suspended ──→ Restored ──→ Approved
```

- **Pending**: Awaiting admin approval
- **Approved**: Full access to Cargo
- **Rejected**: Registration declined (cannot restore directly)
- **Revoked**: Access removed by admin (can be restored)
- **Suspended**: Temporarily disabled (can be restored)

## Admin Dashboard

Access at `/admin` (admin users only)

### Dashboard Overview

- **Stats**: Total users, pending, approved, rejected, revoked, suspended counts
- **Real-time Updates**: Stats refresh every 5 seconds

### User Management

- **Search**: Find users by email or name
- **Filter**: By account status (pending, approved, etc.)
- **Pagination**: 20 users per page
- **Actions**:
  - Approve pending users
  - Reject with reason
  - Revoke approved access
  - Restore revoked/suspended accounts
  - Suspend temporarily
  - Force logout user sessions
  - View account history

### Audit Log

- **View**: All admin actions with timestamps
- **Filter**: By action type
- **Entries**: Admin name, target user, action, timestamp, details

## Database Schema

### Users Table

```
id              UUID (primary key)
email           String (unique)
full_name       String
password_hash   String (bcrypt)
account_status  String (pending/approved/rejected/revoked/suspended)
is_admin        Boolean
rejected_reason Text (optional)
created_at      DateTime
updated_at      DateTime
```

### Sessions Table

```
id              UUID (primary key)
user_id         UUID (foreign key)
token           String (unique)
expires_at      DateTime
created_at      DateTime
```

### Audit Logs Table

```
id              UUID (primary key)
action          String (created/approved/rejected/revoked/restored/suspended)
admin_id        UUID (foreign key)
target_user_id  UUID (foreign key)
timestamp       DateTime
details         Text
outcome         String
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user (requires auth)

### Protected Routes (require `@auth_required`)

All existing Cargo endpoints now require authentication:
- `POST /api/validate`
- `POST /api/preview`
- `POST /api/generate`
- `POST /api/generate-pdf`
- `POST /api/generate-bulk-pdfs`
- `POST /api/parse-airlines`
- `GET /api/templates`
- `POST /api/templates`
- `GET /api/templates/<id>`
- `DELETE /api/templates/<id>`

### Admin Routes (require `@auth_required` + `@admin_required`)

- `GET /api/admin/stats` - User statistics
- `GET /api/admin/users` - List users (paginated, searchable, filterable)
- `GET /api/admin/users/<id>` - User details and history
- `POST /api/admin/users/<id>/approve` - Approve user
- `POST /api/admin/users/<id>/reject` - Reject user
- `POST /api/admin/users/<id>/revoke` - Revoke access
- `POST /api/admin/users/<id>/restore` - Restore access
- `POST /api/admin/users/<id>/suspend` - Suspend user
- `POST /api/admin/users/<id>/logout` - Force logout
- `GET /api/admin/audit-log` - View audit log

## Security Considerations

### Authentication

- ✅ Passwords hashed with bcrypt
- ✅ Sessions stored server-side
- ✅ Tokens validated on every protected request
- ✅ Rate limiting on login (5 attempts/min)
- ✅ Immediate session invalidation on revocation

### Authorization

- ✅ User status checked server-side
- ✅ Admin privilege verified on admin routes
- ✅ No unauthorized access via old tokens
- ✅ All admin actions logged

### Data Protection

- ✅ No plaintext passwords in database or logs
- ✅ Input validation on all forms
- ✅ SQL injection prevention via ORM
- ✅ XSS prevention via template auto-escaping
- ✅ CSRF protection on state-changing requests

### Production Deployment

**Before going to production:**

1. Set `FLASK_SECRET_KEY` to a strong random value
2. Set `FLASK_DEBUG=False`
3. Use HTTPS (set secure cookies)
4. Store `.env` securely (not in version control)
5. Use a production WSGI server (Gunicorn, uWSGI)
6. Set database to production database (PostgreSQL, MySQL)
7. Enable rate limiting on all public endpoints
8. Implement backup/recovery procedures

### Production WSGI Server

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Testing

### Manual Testing Checklist

- [ ] New user can register
- [ ] Registered user cannot access Cargo (pending status)
- [ ] Admin can see pending user in dashboard
- [ ] Admin can approve user
- [ ] Approved user can login
- [ ] Approved user can use Cargo (generate content, PDFs, templates)
- [ ] Admin can revoke user access
- [ ] Revoked user cannot access Cargo
- [ ] Revoked user sees revoked message
- [ ] Admin can restore revoked user
- [ ] Restored user can login again
- [ ] Admin can suspend user
- [ ] Suspended user cannot access Cargo
- [ ] Admin can restore suspended user
- [ ] Admin audit log shows all actions
- [ ] Existing Cargo features work (content generation, PDFs, templates)
- [ ] Multiple users can use Cargo simultaneously

### Automated Testing

Run tests with:

```bash
python tests.py
```

Key test coverage:
- Authentication (register, login, verify)
- Status transitions (pending → approved → revoked)
- Session invalidation
- Admin actions
- Protected routes
- Audit logging
- Existing features

## Troubleshooting

### User cannot login

1. Check account status: Admin dashboard → User Management
2. Ensure account is `approved`
3. Verify correct password
4. Check rate limiting (max 5 attempts/min)

### Session expires quickly

- Default: 15 minutes (900 seconds)
- Change `SESSION_TIMEOUT` in `.env`
- Longer timeouts = less secure

### Cannot access admin dashboard

1. Login as admin user
2. Verify `is_admin` flag in database
3. Check `/admin` shows admin-only content

### Database errors

1. Verify SQLite file exists: `cargo.db`
2. Check file permissions
3. Delete `cargo.db` and reinitialize: `python -c "from app import app, db; app.app_context().push(); db.create_all()"`

### Audit log not showing actions

1. Verify admin user has `is_admin=True`
2. Check audit log in admin dashboard
3. Verify action was performed by authenticated admin

## File Structure

```
cargo/
├── app.py                           # Flask app with auth routes
├── config.py                        # Configuration + database
├── requirements.txt                 # Dependencies
├── .env.example                     # Environment template
│
├── services/
│   ├── models.py                    # SQLAlchemy models
│   ├── auth_service.py              # Authentication logic
│   ├── admin_service.py             # Admin operations
│   ├── decorators.py                # Auth decorators
│   ├── replacement.py               # (existing)
│   ├── pdf_generator.py             # (existing)
│   ├── validation.py                # (existing)
│   └── template_manager.py          # (existing)
│
├── scripts/
│   └── init_admin.py                # Admin bootstrap script
│
├── templates/
│   ├── index.html                   # Main app (updated for auth)
│   ├── login.html                   # Login page
│   ├── register.html                # Registration page
│   ├── admin.html                   # Admin dashboard
│   ├── pending.html                 # Pending approval message
│   ├── rejected.html                # Rejected message
│   ├── revoked.html                 # Revoked message
│   └── suspended.html               # Suspended message
│
├── static/
│   ├── css/
│   │   ├── styles.css               # (existing)
│   │   ├── auth.css                 # Auth pages styling
│   │   └── admin.css                # Admin dashboard styling
│   └── js/
│       ├── main.js                  # (updated for auth)
│       ├── generator.js             # (updated for auth)
│       ├── clipboard.js             # (existing)
│       └── admin.js                 # Admin functionality
│
└── cargo.db                         # SQLite database (auto-created)
```

## Support

For issues, questions, or feature requests, contact the administrator.

---

**Created with 🧠 by Ravi**

## Authentication & Admin Management Implementation Complete

All authentication, user management, and admin controls have been successfully integrated into Cargo while preserving existing functionality.
