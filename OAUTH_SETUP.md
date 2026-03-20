# Google OAuth & User History Setup Guide

## Overview

Your Code Reviewer app now includes:
- ✅ **Google OAuth Authentication** - Users can sign in with Google
- ✅ **Chat History** - All conversations are saved per user
- ✅ **Code Submission History** - Track all code submissions
- ✅ **Review Reports** - Store generated reports
- ✅ **User Dashboard Ready** - Retrieve full user history via API

## Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `django-allauth` - OAuth provider
- `google-auth` and `google-auth-oauthlib` - Google authentication

### Step 2: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google+ API**
4. Create an **OAuth 2.0 Client ID** (Application type: Web Application)
5. Add Authorized JavaScript origins:
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`
   - `https://yourdomain.com` (for production)

6. Add Authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `https://yourdomain.com/accounts/google/login/callback/`

7. Copy the **Client ID** and **Client Secret**

### Step 3: Update .env File

```env
GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID_HERE
GOOGLE_OAUTH_SECRET=YOUR_CLIENT_SECRET_HERE
```

### Step 4: Run Migrations

```bash
python manage.py migrate
```

This creates tables for:
- `UserProfile` - Extended user info with Google ID
- `CodeSubmission` - Stores user code
- `ChatMessage` - Stores conversation history  
- `ReviewReport` - Stores generated reports

### Step 5: Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### Step 6: Start Server

```bash
python manage.py runserver
```

Visit: `http://localhost:8000/`

## Using Google OAuth

### Frontend Login (HTML)

Add this to your navbar/header:

```html
{% if user.is_authenticated %}
    <p>Welcome, {{ user.email }}!</p>
    <a href="{% url 'account_logout' %}">Logout</a>
{% else %}
    <a href="{% url 'socialaccount_login' 'google' %}">Sign in with Google</a>
{% endif %}
```

### Login Flow

1. User clicks "Sign in with Google"
2. Redirected to Google consent screen
3. After consent, returns to your app
4. User automatically logged in
5. `UserProfile` created with Google ID

## User History API Endpoints

### 1. Get All User History

**Endpoint:** `GET /api/history/`

**Requires:** Authentication (logged in)

**Response:**
```json
{
    "code_submissions": [
        {
            "id": 1,
            "title": "Python Bug Fix",
            "language": "python",
            "created_at": "2026-03-20T17:30:00Z"
        }
    ],
    "chat_messages": [
        {
            "id": 1,
            "code_submission_id": 1,
            "role": "user",
            "content": "Fix this bug",
            "action": "find_error",
            "created_at": "2026-03-20T17:31:00Z"
        }
    ],
    "review_reports": [
        {
            "id": 1,
            "code_submission_id": 1,
            "created_at": "2026-03-20T17:32:00Z"
        }
    ]
}
```

### 2. Get Submission Details

**Endpoint:** `GET /api/history/<submission_id>/`

**Requires:** Authentication (must be submission owner)

**Response:**
```json
{
    "code": "def hello():\n    print('world')",
    "language": "python",
    "title": "Hello World",
    "created_at": "2026-03-20T17:30:00Z",
    "chat_messages": [
        {
            "role": "user",
            "content": "Review this code",
            "action": "chat",
            "created_at": "2026-03-20T17:31:00Z"
        },
        {
            "role": "assistant",
            "content": "This is good code!",
            "action": "chat",
            "created_at": "2026-03-20T17:31:05Z"
        }
    ],
    "report": {
        "content": "Full report content...",
        "created_at": "2026-03-20T17:32:00Z"
    }
}
```

## Admin Dashboard

Access Django Admin: `http://localhost:8000/admin/`

You can:
- View all users and their profiles
- Browse code submissions
- View chat conversations
- Check review reports
- Monitor user activity

## Database Models

### UserProfile
```
- user: ForeignKey(User)
- google_id: CharField (unique)
- profile_picture: URLField
- total_reviews: Integer
- created_at: DateTime
- updated_at: DateTime
```

### CodeSubmission
```
- user: ForeignKey(User)
- code: TextField
- language: CharField
- title: CharField
- created_at: DateTime
- updated_at: DateTime
```

### ChatMessage
```
- user: ForeignKey(User)
- code_submission: ForeignKey(CodeSubmission)
- role: CharField (user/assistant)
- content: TextField
- action: CharField (chat/find_error/create_report)
- model_used: CharField
- created_at: DateTime
```

### ReviewReport
```
- user: ForeignKey(User)
- code_submission: OneToOneField(CodeSubmission)
- report_content: TextField
- pdf_file: FileField
- created_at: DateTime
- updated_at: DateTime
```

## Switching Between Databases

### Use Neon (Production)

Uncomment in `.env`:
```env
DATABASE_URL=postgresql://user:password@host:5432/db
```

### Use SQLite (Development)

Comment out in `.env`:
```env
# DATABASE_URL=postgresql://...
```

## Frontend Integration

### Example: Display User History in JavaScript

```javascript
// Get user history
async function loadUserHistory() {
    const response = await fetch('/api/history/');
    if (!response.ok) {
        console.log('User not authenticated');
        return;
    }
    
    const data = await response.json();
    console.log('Code submissions:', data.code_submissions);
    console.log('Chat messages:', data.chat_messages);
    console.log('Reports:', data.review_reports);
}

// Get specific submission
async function loadSubmissionDetails(submissionId) {
    const response = await fetch(`/api/history/${submissionId}/`);
    const data = await response.json();
    console.log('Code:', data.code);
    console.log('Chat history:', data.chat_messages);
    console.log('Report:', data.report);
}
```

## Troubleshooting

### "Redirect URI mismatch" Error
- Check OAuth credentials in `.env`
- Ensure redirect URLs match exactly in Google Cloud Console
- Include `/` at the end: `/accounts/google/login/callback/`

### "Authentication required" on API
- Add `@login_required` decorator to views
- User must be logged in to access `/api/history/`
- Anonymous users get 302 redirect to login

### Database connection issues
- If using Neon, verify DATABASE_URL is set
- If using SQLite, ensure DATABASE_URL is commented out
- Run `python manage.py migrate` to initialize tables

### Chat history not saving
- User must be authenticated
- CodeSubmission must exist before ChatMessage
- Check `request.user.is_authenticated` in views

## Next Steps

1. **Frontend Dashboard:**
   - Create a user dashboard page showing history
   - Display chat sessions with code submissions
   - Show past reports and PDFs

2. **Additional Features:**
   - User profile customization
   - Public/Private code sharing
   - Collaboration features
   - Search through history

3. **Production Deployment:**
   - Set `DJANGO_DEBUG=false`
   - Configure allowed hosts
   - Switch to Neon database
   - Set secure CSRF settings

## Security Notes

- Never expose `GOOGLE_OAUTH_SECRET` in frontend code
- Always use HTTPS in production
- Set `SECURE_SSL_REDIRECT=True` in production settings
- Use environment variables for all secrets
- Implement rate limiting on API endpoints

## Support

For issues with:
- **Django-Allauth:** [Docs](https://django-allauth.readthedocs.io/)
- **Google Auth:** [Google Cloud Docs](https://cloud.google.com/docs)
- **Django:** [Django Docs](https://docs.djangoproject.com/)
