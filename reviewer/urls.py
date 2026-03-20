from django.urls import path

from . import views

app_name = "reviewer"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/review/", views.review_code, name="review_code"),
    path("api/run/", views.run_code, name="run_code"),
    path("api/report/pdf/", views.download_pdf, name="download_pdf"),
    path("api/history/", views.get_user_history, name="get_user_history"),
    path("api/history/<int:submission_id>/", views.get_submission_details, name="get_submission_details"),
]
