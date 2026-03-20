# Code Reviewer Studio

A student-friendly Django project that reviews code with the Gemini API.

## Features

- Left panel for chat, model selection, language selection, and quick actions
- Middle panel code editor
- Right panel terminal runner for Python and JavaScript when available
- Quick actions for finding errors and creating a full report
- PDF export for the latest AI review

## Tech stack

- Django
- HTML
- CSS
- JavaScript
- Gemini API

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
