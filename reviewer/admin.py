from __future__ import annotations

from django.contrib import admin

from .models import ChatMessage, CodeSubmission, ReviewReport, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "google_id", "total_reviews", "created_at")
    search_fields = ("user__username", "user__email", "google_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "language", "created_at")
    list_filter = ("language", "created_at")
    search_fields = ("user__username", "title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "action", "model_used", "created_at")
    list_filter = ("role", "action", "created_at")
    search_fields = ("user__username", "content")
    readonly_fields = ("created_at",)


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ("user", "code_submission", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "code_submission__title")
    readonly_fields = ("created_at", "updated_at")
