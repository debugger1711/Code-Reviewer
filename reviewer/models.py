from __future__ import annotations

from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Extended user profile for Code Reviewer app"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.URLField(blank=True, null=True)
    total_reviews = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.user.username} Profile"


class CodeSubmission(models.Model):
    """Store user code submissions"""
    LANGUAGE_CHOICES = [
        ("python", "Python"),
        ("javascript", "JavaScript"),
        ("cpp", "C++"),
        ("java", "Java"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="code_submissions")
    code = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default="python")
    title = models.CharField(max_length=255, blank=True, default="Untitled")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.title or 'Untitled'} ({self.language})"


class ChatMessage(models.Model):
    """Store chat history between user and AI"""
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    code_submission = models.ForeignKey(
        CodeSubmission,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    action = models.CharField(
        max_length=50,
        choices=[
            ("chat", "Chat"),
            ("find_error", "Find Error"),
            ("create_report", "Create Report"),
        ],
        default="chat",
    )
    model_used = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.role} ({self.action})"


class ReviewReport(models.Model):
    """Store generated review reports"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_reports")
    code_submission = models.OneToOneField(
        CodeSubmission,
        on_delete=models.CASCADE,
        related_name="review_report",
    )
    report_content = models.TextField()
    pdf_file = models.FileField(upload_to="reports/%Y/%m/%d/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Report for {self.code_submission.title} - {self.user.username}"
