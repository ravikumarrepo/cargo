# Deploy Cargo to GitHub & Render

## 🚀 **Option A: GitHub + Render** (RECOMMENDED)

This is the easiest and most reliable combination. Render auto-deploys whenever you push to GitHub.

---

## **Step 1: Push Code to GitHub**

### 1.1 Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `cargo` (or your preferred name)
3. Description: "Cargo - Bulk Content & PDF Generator"
4. Choose: **Public** or **Private**
5. Click "Create repository"

### 1.2 Push Your Code

```bash
cd "C:\Users\ravik\OneDrive\Desktop\pdf generat"

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Cargo with authentication system"

# Add remote (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/cargo.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 1.3 Create .gitignore

Create a `.gitignore` file so sensitive files aren't committed:

```
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/

# Database
cargo.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temp files
temp/
temp_*
*.tmp

# Generated PDFs
generated_pdfs/

# Logs
*.log
```

**Important**: Before pushing, delete `.env` file (if it exists) and only commit `.env.example`

```bash
git rm --cached .env  # Remove from git history
git add .gitignore
git commit -m "Add gitignore and remove .env"
git push
```

---

## **Step 2: Deploy to Render**

### 2.1 Create Render Account

1. Go to https://render.com
2. Click "Sign up"
3. Sign up with GitHub (easiest)
4. Grant permissions

### 2.2 Create New Web Service

1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Click "Connect" next to your GitHub repo
4. Select `cargo` repository
5. Click "Connect"

### 2.3 Configure Deployment

Fill in the form:

| Field | Value |
|-------|-------|
| **Name** | cargo (or your app name) |
| **Environment** | Python 3 |
| **Region** | Choose closest to you |
| **Branch** | main |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |

### 2.4 Set Environment Variables

Scroll down to "Environment" section. Add these variables:

```
ADMIN_EMAIL = dmtoravi@gmail.com
ADMIN_PASSWORD = ravi993440@
FLASK_SECRET_KEY = (generate random - see below)
FLASK_DEBUG = False
DATABASE_URL = sqlite:///cargo.db
SESSION_TIMEOUT = 900
REFRESH_TOKEN_EXPIRY = 604800
```

**Generate FLASK_SECRET_KEY**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.5 Deploy

1. Click "Create Web Service"
2. Render starts building (takes 2-3 minutes)
3. Watch logs in real-time
4. When done, you get a URL like: `cargo-xyz.onrender.com`

### 2.6 Initialize Database

Once deployed, click "Shell" tab and run:

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
python scripts/init_admin.py
```

Or use Render's "Onetime" task feature if Shell isn't available.

---

## **Step 3: Setup Custom Domain (Optional)**

1. In Render dashboard → Settings
2. Scroll to "Custom Domain"
3. Enter your domain (e.g., `cargo.yourdomain.com`)
4. Add DNS records as shown

---

## 📋 **Complete Setup Checklist**

### Before Pushing to GitHub
- [ ] Create `.gitignore`
- [ ] Remove `.env` from git
- [ ] Keep only `.env.example`
- [ ] Add `Procfile` with: `web: gunicorn app:app`
- [ ] Add `runtime.txt` with: `python-3.11.7`

### Render Configuration
- [ ] Connected GitHub repo
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set Start Command: `gunicorn app:app`
- [ ] Added all environment variables
- [ ] Generated strong `FLASK_SECRET_KEY`

### After Deployment
- [ ] Database initialized
- [ ] Admin account created
- [ ] Can login with admin credentials
- [ ] Test creating a user
- [ ] Test admin dashboard

---

## 🚀 **Complete Step-by-Step Walkthrough**

### **Step A: Prepare Your Code**

```bash
# 1. Navigate to your project
cd "C:\Users\ravik\OneDrive\Desktop\pdf generat"

# 2. Install gunicorn
pip install gunicorn

# 3. Update requirements.txt
pip freeze > requirements.txt

# 4. Create Procfile (copy-paste this exactly)
# Create a file named "Procfile" with this content:
web: gunicorn app:app

# 5. Create runtime.txt
# Create a file named "runtime.txt" with:
python-3.11.7

# 6. Create .gitignore (copy from above section)
# 7. Remove .env file if it exists
del .env

# 8. Test locally
python app.py
# Should start without errors
```

### **Step B: Push to GitHub**

```bash
# 1. Initialize git
git init

# 2. Add all files
git add .

# 3. Create commit
git commit -m "Initial commit: Cargo with full authentication system"

# 4. Create main branch
git branch -M main

# 5. Add GitHub remote (REPLACE YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/cargo.git

# 6. Push to GitHub
git push -u origin main

# 7. Verify on GitHub
# Go to https://github.com/YOUR_USERNAME/cargo
# You should see all your files
```

### **Step C: Deploy to Render**

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect your `cargo` GitHub repo
5. Configure:
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn app:app`
6. Add environment variables (see above)
7. Click "Create Web Service"
8. Wait 2-3 minutes for build
9. Get your URL: `https://cargo-xyz.onrender.com`

### **Step D: Initialize on Render**

After app is live, click "Shell" tab and run:

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('DB created')"
python scripts/init_admin.py
```

### **Step E: Login & Test**

1. Go to your Render URL
2. You'll be redirected to login
3. Enter credentials:
   - Email: `dmtoravi@gmail.com`
   - Password: `ravi993440@`
4. Click "Admin" button
5. Test admin dashboard

---

## 📁 **Final File Structure**

Your GitHub repo should have:

```
cargo/
├── app.py
├── config.py
├── requirements.txt
├── runtime.txt          ← NEW
├── Procfile             ← NEW
├── .gitignore           ← NEW
├── .env.example         ← KEEP (but not .env)
├── services/
├── templates/
├── static/
├── scripts/
├── AUTHENTICATION.md
├── DEPLOYMENT_GUIDE.md
└── ... (other files)
```

---

## 🔄 **After First Deploy: Updating Your App**

Whenever you make changes locally:

```bash
# 1. Make changes to your code
# 2. Test locally
python app.py

# 3. Commit changes
git add .
git commit -m "Describe your changes"

# 4. Push to GitHub
git push origin main

# 5. Render automatically redeploys!
# Check deployment status in Render dashboard
```

---

## ❌ **Common Issues & Fixes**

### **Build Failed: Module not found**
- Add missing package to `requirements.txt`
- Run: `pip freeze > requirements.txt`
- Commit and push

### **App crashes on startup**
- Check Render logs
- Verify environment variables are set
- Check database initialized

### **Can't login**
- Verify admin account created in Shell
- Check email and password match
- Review app logs in Render

### **Static files not loading**
- Usually works automatically with Render
- Check Nginx/Flask is serving static files
- Verify paths are correct

### **Database errors**
- In Render Shell, run:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## 🎯 **Comparison: GitHub + Render vs Others**

| Feature | GitHub + Render | Heroku | Railway |
|---------|-----------------|--------|---------|
| **Ease** | ⭐⭐⭐⭐⭐ Very Easy | ⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐⭐ Easiest |
| **Cost** | Free | Free (limited) | Free (limited) |
| **Performance** | Excellent | Good | Excellent |
| **Auto-deploy** | Yes | Yes | Yes |
| **Uptime** | 99.95% | 99.9% | 99.9% |
| **Support** | Good | Excellent | Good |

---

## 💡 **Pro Tips**

1. **Use GitHub for version control**
   - Keeps history of all changes
   - Easy to rollback if needed
   - Collaborate with others

2. **Render auto-deploys on git push**
   - No need to manually deploy
   - Just push to GitHub and it's live

3. **Keep `.env.example` in repo**
   - Shows what env vars are needed
   - Never commit actual `.env`

4. **Monitor Render logs**
   - Click "Logs" in Render dashboard
   - See any errors in real-time

5. **Use free tier during development**
   - Render free tier is generous
   - Upgrade when you need more

---

## 📞 **Support Links**

- **GitHub Help**: https://docs.github.com
- **Render Docs**: https://render.com/docs
- **Python Deployment**: https://pythonbytes.fm

---

## ✅ **You're Ready!**

Follow the steps above and your Cargo app will be live on the internet in 15-20 minutes!

**Summary**:
1. ✅ Prepare code (add Procfile, runtime.txt, requirements.txt)
2. ✅ Push to GitHub
3. ✅ Deploy to Render
4. ✅ Initialize database
5. ✅ Login and enjoy!

🎉 **Your app is now online!**
