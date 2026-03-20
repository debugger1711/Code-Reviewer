# Code Reviewer Studio 🚀

A modern, AI-powered code review application built with **Django 5.2**, **Google OAuth 2.0**, and **Google Gemini AI**. Features a dark glassmorphic UI, automatic code history tracking, and PDF report generation.

![Django](https://img.shields.io/badge/Django-5.2.12-green)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **🤖 AI Code Review** - Analyze code with Google Gemini AI for bugs, improvements, and explanations
- **🔐 Google OAuth 2.0** - Secure authentication with automatic user profile creation
- **📊 Automatic History** - All reviews, chats, and reports auto-saved to database
- **📄 PDF Reports** - Generate styled PDF reports with code analysis
- **🎨 Dark Glassmorphic UI** - Modern purple/orange theme with smooth animations
- **💬 Interactive Chat** - Ask AI detailed questions about your code
- **⚡ Multi-Language Support** - Python, JavaScript, Java, C++, Go, Rust, and more
- **🗄️ User Data Persistence** - Store submissions, chat history, and reports per user
- **🔄 Flexible Database** - SQLite (development) or PostgreSQL Neon (production)

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Django 5.2.12 |
| Authentication | Google OAuth 2.0 (django-allauth) |
| AI Engine | Google Gemini API |
| Database | SQLite / PostgreSQL Neon |
| Frontend | HTML5, CSS3 (Glassmorphism), JavaScript |
| PDF Generation | ReportLab |

## 📋 Requirements

- Python 3.10+
- pip or conda
- Google Cloud account (for OAuth & Gemini API)
- Neon PostgreSQL account (optional, for production)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/Code-Reviewer.git
cd Code-Reviewer
```

### 2. Setup Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
# Google OAuth (get from Google Cloud Console)
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_SECRET=your_client_secret

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Optional: PostgreSQL (Neon)
# DATABASE_URL=postgresql://user:password@host/database
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Admin User (Optional)
```bash
python manage.py createsuperuser
```

### 7. Start Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## 📚 Setup Guides

### Getting Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`
6. Copy Client ID and Secret to `.env`

### Getting Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy key to `.env` as `GEMINI_API_KEY`

### Using PostgreSQL (Production)
1. Create Neon project at [neon.tech](https://neon.tech)
2. Copy connection string
3. Add to `.env`: `DATABASE_URL=postgresql://...`
4. Run migrations: `python manage.py migrate`

## 📁 Project Structure

```
Code-Reviewer/
├── codereviewer/          # Main project settings
│   ├── settings.py        # Django configuration
│   ├── urls.py            # Root URL routing
│   └── wsgi.py            # WSGI configuration
├── reviewer/              # Main app
│   ├── models.py          # Database models (User submissions, Chat history, Reports)
│   ├── views.py           # API endpoints
│   ├── services.py        # Gemini AI integration
│   ├── pdf_utils.py       # PDF generation
│   ├── urls.py            # App URL routing
│   ├── templates/
│   │   └── reviewer/index.html    # Main UI template
│   └── static/
│       └── reviewer/
│           ├── style.css          # Dark theme styling
│           └── script.js          # Frontend logic
├── requirements.txt       # Python dependencies
├── manage.py             # Django CLI
├── db.sqlite3            # Local database (dev)
└── README.md             # This file
```

## 📊 Data Models

### UserProfile
- Stores Google OAuth ID and profile picture
- Tracks total reviews per user

### CodeSubmission
- User's submitted code with language and title
- Linked to all related chat messages and reports

### ChatMessage
- Stores conversation history (user prompts & AI responses)
- Tracks action type and model used

### ReviewReport
- Stores generated PDF reports
- Linked to code submission

## 🔌 API Endpoints

### Authentication
- `GET /accounts/google/login/` - Google OAuth login
- `GET /accounts/logout/` - Logout user

### Code Review
- `POST /api/review/` - Submit code for review
- `POST /api/report/pdf/` - Generate PDF report

### History (Login Required)
- `GET /api/history/` - Get all user submissions and messages
- `GET /api/history/<id>/` - Get specific submission with chat thread

## 🎯 Usage Examples

### Review Code via UI
1. Click "🔐 Sign in with Google" (top-right)
2. Authorize with Google account
3. Paste code in editor
4. Select language and model
5. Click "💬 Ask AI" or enter custom prompt
6. Click "📥 PDF Export" to download report

### Review Code via API
```bash
curl -X POST http://127.0.0.1:8000/api/review/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello(): print(\"world\")",
    "language": "python",
    "prompt": "Review this code",
    "action": "chat",
    "model": "gemini-2.0-flash"
  }'
```

### Get User History
```bash
curl http://127.0.0.1:8000/api/history/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🌐 Deployment

### Using Heroku
```bash
heroku create your-app-name
heroku config:set GEMINI_API_KEY=your_key
heroku config:set GOOGLE_OAUTH_CLIENT_ID=your_id
heroku config:set GOOGLE_OAUTH_SECRET=your_secret
git push heroku main
heroku run python manage.py migrate
```

### Using PythonAnywhere
1. Upload repository
2. Set environment variables in Web app settings
3. Configure WSGI file
4. Run collectstatic

### Using Docker
```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "codereviewer.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🐛 Troubleshooting

### OAuth Not Working
- Verify Google Cloud credentials are correct
- Check redirect URI matches exactly: `http://localhost:8000/accounts/google/login/callback/`
- Clear browser cookies and try again

### History Not Saving
- Ensure user is authenticated (login first)
- Check database migrations: `python manage.py showmigrations`
- Verify INSTALLED_APPS includes allauth

### Database Issues
- Reset SQLite: `rm db.sqlite3` then `python manage.py migrate`
- For Neon: Verify DATABASE_URL and network connectivity

## 📝 Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Django Admin
Access at `http://127.0.0.1:8000/admin/` with superuser credentials.

## 🔒 Security Notes

- Never commit `.env` with real credentials
- Use environment variables for sensitive data
- Set `DEBUG=False` in production
- Use strong `SECRET_KEY`
- Enable HTTPS and CSRF protection
- Rate limit API endpoints

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Support

- Issues: [GitHub Issues](https://github.com/yourusername/Code-Reviewer/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/Code-Reviewer/discussions)

## 🙏 Acknowledgments

- Django framework
- Google Gemini AI
- django-allauth for OAuth integration
- ReportLab for PDF generation

---

**Made with ❤️ for code reviewers everywhere**

Last Updated: March 20, 2026

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Add your environment variables in `.env`:

```env
DJANGO_SECRET_KEY=your-generated-secret-key
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
GEMINI_API_KEY=your-gemini-api-key
GEMINI_DEFAULT_MODEL=gemini-2.5-flash
```

4. Run migrations:

```powershell
python manage.py migrate
```

5. Start the server:

```powershell
python manage.py runserver
```

6. Open `http://127.0.0.1:8000/`

## Notes

- The terminal panel executes Python directly with the same interpreter used for Django.
- JavaScript execution requires `node` to be installed.
- C++ and Java are available as review languages in the prompt, but execution is not configured by default.
