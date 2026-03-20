# 🔐 Google OAuth Fix Guide

## Issue Found

Google OAuth was not fully configured. Here's what was missing:

### ✅ What Was Already Working:
1. ✓ `django-allauth` installed and configured
2. ✓ Settings.py has OAuth configuration
3. ✓ Environment variables set (.env has credentials)
4. ✓ URLs configured for OAuth flow
5. ✓ Database migrations applied

### ❌ What Was Missing:
1. ✗ Google OAuth SocialApp NOT registered in Django database
2. ✗ Site domain not updated to match development environment

---

## 🔧 Fix Applied

I've created setup scripts to automatically configure this:

### Step 1: Create OAuth SocialApp ✓
```bash
python setup_oauth.py
```
This:
- Registers Google as a SocialApp in the database
- Links Google credentials from .env
- Creates the database entry needed for OAuth

**Result:**
```
✓ Created Google OAuth SocialApp
  Client ID: 973757269237-74ppu793hljffksfk7j7lmsonq7...
  Site: example.com
```

### Step 2: Update Site Domain ✓
```bash
python update_site.py
```
This:
- Updates Django's default Site from `example.com` to `127.0.0.1:8000`
- Matches your local development environment
- Required for OAuth callback to work

**Result:**
```
Updated Site Domain: 127.0.0.1
✓ OAuth is now configured!
```

---

## 🚀 Test if OAuth Works Now

1. **Start the server:**
   ```bash
   python manage.py runserver
   ```

2. **Go to:** `http://127.0.0.1:8000/`

3. **Click the Google login button** (🔐 Sign in with Google)

4. **You should see:**
   - Google consent screen
   - Redirect back to your app
   - Welcome message with your email

---

## 📋 Quick Checklist

- [x] Google credentials in .env file
- [x] django-allauth installed
- [x] Migrations applied
- [x] SocialApp created in database
- [x] Site domain updated
- [x] OAuth URLs configured

---

## 🐛 If Still Not Working

### Common Issues & Fixes:

**Issue 1: "Client ID Mismatch"**
- Go to http://127.0.0.1:8000/admin/
- Check if Site domain matches (should be `127.0.0.1:8000`)
- Check SocialApplication has correct Client ID

**Issue 2: "Invalid Redirect URI"** 
- Ensure Google Cloud Console has approved redirect URI:
  - `http://127.0.0.1:8000/accounts/google/login/callback/`
- Site domain in Django must match

**Issue 3: Still getting errors**
- Run: `python manage.py migrate` (ensure all migrations applied)
- Clear browser cache and cookies
- Restart server: `Ctrl+C` then `python manage.py runserver`

---

## 📊 Admin Panel Setup

1. Create superuser if not done:
   ```bash
   python manage.py createsuperuser
   ```

2. Go to: `http://127.0.0.1:8000/admin/`

3. Check these sections:
   - **Sites**: Should show `127.0.0.1:8000` ✓
   - **Social Applications**: Should show `Google` with your credentials ✓

4. If missing, you can add them manually through admin interface

---

## 🔄 Manual Setup (if scripts fail)

### Via Django Admin:

1. **Go to:** http://127.0.0.1:8000/admin/

2. **Go to Sites:**
   - Edit the existing site
   - Domain: `127.0.0.1:8000`
   - Name: `Code Reviewer`
   - Save

3. **Go to Social Applications:**
   - Click "Add Social Application"
   - Provider: Google
   - Name: Google OAuth
   - Client ID: (from Google Cloud Console)
   - Secret Key: (from Google Cloud Console)
   - Sites: Select `127.0.0.1:8000`
   - Save

---

## ✨ After OAuth is Working

1. Create test user account with Google login
2. Your `UserProfile` will auto-create
3. Chat history and code submissions will auto-save
4. Access history at: `/api/history/`

---

## 📞 Full Reset (if needed)

If you want to start fresh:

```bash
# 1. Delete the database
del db.sqlite3

# 2. Run migrations again
python manage.py migrate

# 3. Create superuser
python manage.py createsuperuser

# 4. Setup OAuth
python setup_oauth.py

# 5. Update site
python update_site.py

# 6. Start server
python manage.py runserver
```

---

**Status: Google OAuth should now be working! 🎉**

Try logging in with Google to test!
