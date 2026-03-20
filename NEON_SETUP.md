# Neon Database Setup Guide

## Overview
The application has been configured to support **Neon DB** (PostgreSQL) for production and **SQLite3** for local development.

## Changes Made

### 1. **Dependencies Updated** (`requirements.txt`)
   - Added `psycopg2-binary>=2.9.0` for PostgreSQL support

### 2. **Database Configuration** (`codereviewer/settings.py`)
   - Implemented smart database routing:
     - If `DATABASE_URL` environment variable is set → Uses **PostgreSQL (Neon)**
     - If `DATABASE_URL` is not set → Uses **SQLite3** (local development)
   - Uses proper URL parsing with `urllib.parse.urlparse`
   - SSL mode enabled for secure connection to Neon
   - Connection pooling configured (`CONN_MAX_AGE=600`)

### 3. **Environment Variables** (`.env` file)
   ```
   DATABASE_URL=postgresql://user:password@host.neon.tech:5432/dbname
   GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
   ```

## Setup Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Get Your Neon Database URL

1. Go to [Neon Console](https://console.neon.tech)
2. Create a new project or select existing one
3. Copy the **Connection String** (it looks like):
   ```
   postgresql://neondb_owner:password@ep-xyz.neon.tech:5432/neondb
   ```

### Step 3: Update `.env` File

Replace the placeholders in `.env`:

```env
# Before:
DATABASE_URL=postgresql://user:password@host.neon.tech:5432/dbname
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

# After (Example):
DATABASE_URL=postgresql://neondb_owner:abc123xyz@ep-xyz.neon.tech:5432/neondb
GEMINI_API_KEY=AIzaSyA8OEDmtGTGYLLnXweDLuYGa5yZj_s6s8U
```

### Step 4: Run Migrations
```bash
python manage.py migrate
```

### Step 5: Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### Step 6: Run the Server
```bash
python manage.py runserver
```

## Development Mode (SQLite3)

If you want to use local SQLite3 during development:
- Simply **don't set** the `DATABASE_URL` environment variable
- Or comment it out in `.env`:
  ```env
  # DATABASE_URL=postgresql://user:password@host.neon.tech:5432/dbname
  ```

The application will automatically fall back to SQLite3 (`db.sqlite3`).

## Gemini API Key

Replace `YOUR_GEMINI_API_KEY_HERE` in `.env` with your actual Gemini API key from:
- [Google AI Studio](https://aistudio.google.com/app/apikey)

## Switching Between Databases

- **To use Neon (Production)**: Set `DATABASE_URL` in `.env`
- **To use SQLite (Development)**: Leave `DATABASE_URL` unset/commented

## Troubleshooting

### Connection Refused Error
- Verify Neon database is active
- Check if DATABASE_URL is correct
- Ensure SSL mode is enabled in Neon settings

### Migration Issues
```bash
# Reset migrations (development only!)
python manage.py migrate --fake-initial
python manage.py migrate
```

### Check Current Database
```bash
python manage.py dbshell
```

## Notes
- Local development uses `db.sqlite3` (not tracked in git)
- Neon provides free tier with 0.5 GB storage
- Connection strings expire periodically - refresh if needed
- SSL is mandatory for Neon connections
