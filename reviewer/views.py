from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import RequestDataTooBig
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import ChatMessage, CodeSubmission, ReviewReport
from .pdf_utils import build_pdf_report
from .services import ReviewService


def _load_json_payload(request: HttpRequest) -> tuple[dict | None, JsonResponse | None]:
    try:
        raw_body = request.body
    except RequestDataTooBig:
        limit_mb = max(1, settings.DATA_UPLOAD_MAX_MEMORY_SIZE // (1024 * 1024))
        return None, JsonResponse(
            {
                "error": (
                    f"Request is too large for the server limit. Keep code plus chat under about {limit_mb} MB, "
                    "or clear previous chat history and try again."
                )
            },
            status=413,
        )

    try:
        return json.loads(raw_body.decode("utf-8")), None
    except json.JSONDecodeError:
        return None, JsonResponse({"error": "Invalid JSON payload."}, status=400)


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "reviewer/index.html",
        {
            "models": settings.GEMINI_MODELS,
            "default_model": settings.GEMINI_DEFAULT_MODEL,
        },
    )


@require_POST
def review_code(request: HttpRequest) -> JsonResponse:
    payload, error_response = _load_json_payload(request)
    if error_response:
        return error_response

    code = payload.get("code", "").strip()
    if not code:
        return JsonResponse({"error": "Please paste code into the editor first."}, status=400)

    service = ReviewService()
    try:
        result = service.review_code(
            code=code,
            action=payload.get("action", "chat"),
            prompt=payload.get("prompt", ""),
            model=payload.get("model", settings.GEMINI_DEFAULT_MODEL),
            language=payload.get("language", "python"),
            history=payload.get("history", []),
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    # Save to database if user is authenticated
    if request.user.is_authenticated:
        try:
            # Save or get code submission
            code_submission, created = CodeSubmission.objects.get_or_create(
                user=request.user,
                code=code,
                language=payload.get("language", "python"),
                defaults={"title": payload.get("title", "Untitled")},
            )

            # Save user message
            ChatMessage.objects.create(
                user=request.user,
                code_submission=code_submission,
                role="user",
                content=payload.get("prompt", ""),
                action=payload.get("action", "chat"),
                model_used=payload.get("model", settings.GEMINI_DEFAULT_MODEL),
            )

            # Save assistant message
            ChatMessage.objects.create(
                user=request.user,
                code_submission=code_submission,
                role="assistant",
                content=result.get("answer", ""),
                action=payload.get("action", "chat"),
                model_used=payload.get("model", settings.GEMINI_DEFAULT_MODEL),
            )
        except Exception as e:
            # Log the error but don't fail the API call
            print(f"Error saving chat history: {e}")

    return JsonResponse(result)


@require_POST
def run_code(request: HttpRequest) -> JsonResponse:
    payload, error_response = _load_json_payload(request)
    if error_response:
        return error_response

    language = payload.get("language", "python")
    code = payload.get("code", "").strip()
    if not code:
        return JsonResponse({"error": "Add code before running it."}, status=400)

    runners = {
        "python": {
            "command": [sys.executable],
            "suffix": ".py",
        },
        "javascript": {
            "command": [shutil.which("node")] if shutil.which("node") else None,
            "suffix": ".js",
        },
    }
    runner = runners.get(language)
    if not runner or not runner["command"]:
        return JsonResponse(
            {
                "output": (
                    f"Execution is not configured for {language} in this environment. "
                    "Use Python or install the required runtime first."
                )
            }
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / f"snippet{runner['suffix']}"
        file_path.write_text(code, encoding="utf-8")

        try:
            completed = subprocess.run(
                [*runner["command"], str(file_path)],
                capture_output=True,
                text=True,
                timeout=settings.TERMINAL_TIMEOUT_SECONDS,
                cwd=temp_dir,
            )
        except subprocess.TimeoutExpired:
            return JsonResponse(
                {
                    "output": (
                        f"Execution stopped after {settings.TERMINAL_TIMEOUT_SECONDS} seconds "
                        "to keep the project responsive."
                    )
                }
            )

    output = completed.stdout.strip()
    errors = completed.stderr.strip()
    status_line = f"Exit code: {completed.returncode}"
    final_output = "\n".join(part for part in [status_line, output, errors] if part)
    return JsonResponse({"output": final_output or "Program finished without output."})


@require_POST
def download_pdf(request: HttpRequest) -> HttpResponse:
    payload, error_response = _load_json_payload(request)
    if error_response:
        return error_response

    answer = payload.get("answer", "").strip()
    if not answer:
        return JsonResponse({"error": "Generate a review before exporting a PDF."}, status=400)

    try:
        pdf_bytes = build_pdf_report(
            title=payload.get("title", "Code Review Report"),
            action=payload.get("action", "chat"),
            language=payload.get("language", "python"),
            answer=answer,
            code=payload.get("code", ""),
        )
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500)

    # Save review report if user is authenticated
    if request.user.is_authenticated:
        try:
            code_submission = CodeSubmission.objects.filter(
                user=request.user,
                code=payload.get("code", ""),
            ).first()
            
            if code_submission:
                ReviewReport.objects.create(
                    user=request.user,
                    code_submission=code_submission,
                    report_content=answer,
                )
        except Exception as e:
            # Log the error but don't fail the PDF download
            print(f"Error saving review report: {e}")

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="code-review-report.pdf"'
    return response


@require_GET
@login_required
def get_user_history(request: HttpRequest) -> JsonResponse:
    """Get user's code submissions and chat history"""
    user = request.user
    
    # Get user's code submissions
    code_submissions = CodeSubmission.objects.filter(user=user).values(
        "id", "title", "language", "created_at"
    )

    # Get user's chat messages grouped by code submission
    chat_messages = ChatMessage.objects.filter(user=user).values(
        "id", "code_submission_id", "role", "content", "action", "created_at"
    )

    # Get user's review reports
    review_reports = ReviewReport.objects.filter(user=user).values(
        "id", "code_submission_id", "created_at"
    )

    return JsonResponse(
        {
            "code_submissions": list(code_submissions),
            "chat_messages": list(chat_messages),
            "review_reports": list(review_reports),
        }
    )


@require_GET
@login_required
def get_submission_details(request: HttpRequest, submission_id: int) -> JsonResponse:
    """Get details of a specific code submission with its chat history"""
    try:
        submission = CodeSubmission.objects.get(id=submission_id, user=request.user)
    except CodeSubmission.DoesNotExist:
        return JsonResponse({"error": "Code submission not found."}, status=404)

    chat_messages = ChatMessage.objects.filter(code_submission=submission).values(
        "role", "content", "action", "created_at"
    )

    report = ReviewReport.objects.filter(code_submission=submission).first()

    return JsonResponse(
        {
            "code": submission.code,
            "language": submission.language,
            "title": submission.title,
            "created_at": submission.created_at.isoformat(),
            "chat_messages": list(chat_messages),
            "report": {
                "content": report.report_content,
                "created_at": report.created_at.isoformat(),
            } if report else None,
        }
    )
