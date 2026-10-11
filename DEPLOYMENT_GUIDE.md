# Cargo - Production Deployment Guide

## Deployment Options

### Option 1: **Heroku** (Easiest, Free tier available)
### Option 2: **Railway** (Simple, affordable)
### Option 3: **PythonAnywhere** (Python-specific hosting)
### Option 4: **DigitalOcean / Linode / AWS** (Full control, paid)
### Option 5: **Google Cloud / Azure** (Enterprise options)

---

## 🚀 **Option 1: Deploy to Heroku** (Recommended for beginners)

### Prerequisites
- Heroku account (free at heroku.com)
- Git installed
- Heroku CLI installed

### Step 1: Install Heroku CLI

**Windows**:
```bash
# Download from: https://devcenter.heroku.com/articles/heroku-cli
# Or use choco
choco install heroku-cli
```

**Mac/Linux**:
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

### Step 2: Create Procfile

Create a file named `Procfile` (no extension) in your project root:

```
web: gunicorn app:app
```

### Step 3: Create runtime.txt

Create `runtime.txt`:

```
python-3.11.7
```

### Step 4: Update requirements.txt

Add Gunicorn:

```bash
pip install gunicorn
pip freeze > requirements.txt
```

Or add this line to requirements.txt:
```
gunicorn==21.2.0
```

### Step 5: Initialize Git Repository

```bash
cd "C:\Users\ravik\OneDrive\Desktop\pdf generat"
git init
git add .
git commit -m "Initial commit: Cargo with authentication"
```

### Step 6: Create Heroku App

```bash
heroku login
heroku create your-app-name
```

Replace `your-app-name` with something unique (e.g., `cargo-app-yourname`)

### Step 7: Set Environment Variables

```bash
heroku config:set ADMIN_EMAIL=dmtoravi@gmail.com
heroku config:set ADMIN_PASSWORD=<set-securely>
heroku config:set FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set FLASK_DEBUG=False
heroku config:set DATABASE_URL=sqlite:///cargo.db
```

### Step 8: Deploy

```bash
git push heroku main
```

(If your branch is `master` instead of `main`, use `master`)

### Step 9: Initialize Database on Heroku

```bash
heroku run python -c "from app import app, db; app.app_context().push(); db.create_all()"
heroku run python scripts/init_admin.py
```

### Step 10: Open Your App

```bash
heroku open
```

Your app is now live! 🎉

---

## 🚀 **Option 2: Deploy to Railway** (Recommended - Free tier)

### Step 1: Create Railway Account
Visit: https://railway.app

### Step 2: Connect GitHub Repository

1. Push your code to GitHub:
```bash
git remote add origin https://github.com/yourusername/cargo.git
git push -u origin main
```

2. In Railway:
   - Click "New Project"
   - Select "Deploy from GitHub"
   - Choose your repository
   - Railway auto-detects it's Python

### Step 3: Add Environment Variables

In Railway dashboard:
```
ADMIN_EMAIL=dmtoravi@gmail.com
ADMIN_PASSWORD=<set-in-dashboard>
FLASK_SECRET_KEY=<generate random>
FLASK_DEBUG=False
DATABASE_URL=sqlite:///cargo.db
```

### Step 4: Add Procfile

```
web: gunicorn app:app
```

### Step 5: Deploy

Railway auto-deploys on push. Check deployment status in dashboard.

### Step 6: Initialize Database

In Railway terminal:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
python scripts/init_admin.py
```

---

## 🚀 **Option 3: Deploy to PythonAnywhere**

### Step 1: Create PythonAnywhere Account
Visit: https://www.pythonanywhere.com

### Step 2: Upload Files

1. Go to "Files" in dashboard
2. Upload your project files or clone from GitHub:
```bash
git clone https://github.com/yourusername/cargo.git
```

### Step 3: Create Virtual Environment

In Bash console:
```bash
mkvirtualenv --python=/usr/bin/python3.11 cargo
pip install -r requirements.txt
```

### Step 4: Create Web App

1. Go to "Web apps"
2. Click "Add a new web app"
3. Choose "Python 3.11" + "Flask"
4. Edit WSGI configuration:

```python
import sys
path = '/home/yourusername/cargo'
if path not in sys.path:
    sys.path.append(path)

from app import app as application
```

### Step 5: Set Environment Variables

In PythonAnywhere bash:
```bash
export ADMIN_EMAIL=dmtoravi@gmail.com
export ADMIN_PASSWORD=<set-in-dashboard>
```

Or edit `.env` file and load it in WSGI.

### Step 6: Initialize Database

```bash
python manage.py db upgrade
python scripts/init_admin.py
```

---

## 🚀 **Option 4: Deploy to DigitalOcean/Linode** (Advanced)

### Prerequisites
- DigitalOcean account
- Created droplet (Ubuntu 22.04)
- SSH access to server

### Step 1: SSH into Server

```bash
ssh root@your_server_ip
```

### Step 2: Install Dependencies

```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx
```

### Step 3: Clone Repository

```bash
git clone https://github.com/yourusername/cargo.git /var/www/cargo
cd /var/www/cargo
```

### Step 4: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### Step 5: Create Systemd Service

Create `/etc/systemd/system/cargo.service`:

```ini
[Unit]
Description=Cargo Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/cargo
Environment="PATH=/var/www/cargo/venv/bin"
Environment="ADMIN_EMAIL=dmtoravi@gmail.com"
Environment="ADMIN_PASSWORD=<set-in-dashboard>"
Environment="FLASK_SECRET_KEY=<generate-random>"
Environment="FLASK_DEBUG=False"
ExecStart=/var/www/cargo/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

### Step 6: Configure Nginx

Create `/etc/nginx/sites-available/cargo`:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /var/www/cargo/static/;
    }
}
```

Enable site:
```bash
ln -s /etc/nginx/sites-available/cargo /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 7: Start Service

```bash
systemctl enable cargo
systemctl start cargo
systemctl status cargo
```

### Step 8: Setup SSL (Let's Encrypt)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your_domain.com
```

### Step 9: Initialize Database

```bash
cd /var/www/cargo
source venv/bin/activate
python -c "from app import app, db; app.app_context().push(); db.create_all()"
python scripts/init_admin.py
```

---

## 🔒 **Security Best Practices**

### Before Going Live

1. **Generate Strong Secret Key**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **Set Environment Variables Securely**
   - Never commit `.env` to git
   - Use hosting platform's secret management

3. **Configure Firewall**
   - Only expose port 80 (HTTP) and 443 (HTTPS)
   - Close all other ports

4. **Enable HTTPS**
   - Use Let's Encrypt (free)
   - Redirect HTTP to HTTPS

5. **Use PostgreSQL/MySQL**
   - SQLite works, but not recommended for production
   - Heroku: Add PostgreSQL add-on
   - DigitalOcean: Create separate database droplet

6. **Backup Database**
   - Set up automated backups
   - Test recovery procedures

7. **Monitor Logs**
   - Set up error tracking (Sentry)
   - Monitor application logs
   - Check server resource usage

### production .env

```env
# SECURITY - Change these!
FLASK_SECRET_KEY=<strong-random-key>
ADMIN_PASSWORD=<strong-admin-password>

# APP
ADMIN_EMAIL=dmtoravi@gmail.com
FLASK_DEBUG=False

# DATABASE - Use PostgreSQL in production
DATABASE_URL=postgresql://user:password@hostname:5432/cargo

# SESSION
SESSION_TIMEOUT=900
REFRESH_TOKEN_EXPIRY=604800

# LOGGING
LOG_LEVEL=INFO
```

---

## 📊 **Production Checklist**

Before deployment:
- [ ] Generate strong `FLASK_SECRET_KEY`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Use strong `ADMIN_PASSWORD`
- [ ] Setup HTTPS/SSL certificate
- [ ] Configure database (PostgreSQL/MySQL)
- [ ] Setup automated backups
- [ ] Configure firewall
- [ ] Set up error monitoring (Sentry)
- [ ] Test all user workflows
- [ ] Test admin dashboard
- [ ] Test revocation/session invalidation
- [ ] Setup monitoring & alerts
- [ ] Document deployment procedure
- [ ] Setup CI/CD pipeline (optional)

---

## 🆘 **Troubleshooting**

### App won't start
```bash
# Check logs
heroku logs --tail
# or
journalctl -u cargo -f
```

### Database errors
- Ensure database initialization ran
- Check database URL is correct
- Verify database has write permissions

### Static files not loading
- Run: `python app.py` locally to test
- Check Nginx configuration (if using Nginx)
- Verify static file paths

### Login not working
- Verify admin account was created
- Check database has users
- Review logs for errors

### Performance issues
- Increase gunicorn workers: `-w 8`
- Enable caching headers
- Use CDN for static files
- Upgrade database plan

---

## 📱 **Domain Setup**

### Point Domain to Heroku
```bash
heroku domains:add www.your-domain.com
```

### Point Domain to DigitalOcean
1. Add A record pointing to droplet IP
2. Add CNAME record for www → @ (your IP)

### DNS Configuration
```
A record:       your-domain.com  →  your_server_ip
CNAME record:   www              →  your-domain.com
```

---

## 🚀 **Quick Deploy Commands**

### Heroku
```bash
git push heroku main
```

### Railway
```bash
git push origin main  # Auto-deploys
```

### DigitalOcean
```bash
git pull /var/www/cargo main
systemctl restart cargo
```

---

## 📞 **Support Resources**

- **Heroku Docs**: https://devcenter.heroku.com
- **Railway Docs**: https://docs.railway.app
- **PythonAnywhere**: https://help.pythonanywhere.com
- **DigitalOcean**: https://docs.digitalocean.com
- **Gunicorn**: https://gunicorn.org
- **Nginx**: https://nginx.org/en/docs

---

## 💡 **Recommended Deployment**

For beginners:
1. **Heroku** (simplest, good for small apps)
2. **Railway** (better pricing, similar ease)

For production:
1. **DigitalOcean** (good balance of price/control)
2. **AWS** (enterprise scale)
3. **Google Cloud** (if already using Google services)

---

## 🎯 **Summary**

1. Choose hosting platform
2. Set up environment variables
3. Configure web server/WSGI
4. Initialize database
5. Create admin account
6. Setup SSL/HTTPS
7. Configure domain
8. Monitor and backup
9. Celebrate! 🎉

Your Cargo app is now online and ready for users!
