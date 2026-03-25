from django.urls import path
from .views import (
    api_chat,
    api_profile,
    api_update_profile,
    api_register,
    api_chat_history,
    api_detect,
    api_history,
    api_feedback,
    api_expense,
    api_expenses,
    api_activities,
    api_activity,
    # template page views
    login_page,
    signup_page,
    dashboard_page,
    chat_page,
    profile_page,
    disease_page,
)


urlpatterns = [
    # -------------------------
    # 🔌 API ENDPOINTS
    # -------------------------
    path("chat/", api_chat),
    path("profile/", api_profile),
    path("profile/update/", api_update_profile),
    path("api/register/", api_register),
    path("chat-history/", api_chat_history),
    # disease detection
    path("disease-detection/", api_detect),
    path("disease-history/", api_history),
    path("disease-feedback/", api_feedback),

    # -------------------------
    # 🧾 Expense tracking
    # -------------------------
    path("expenses/", api_expenses),
    path("expenses/add/", api_expense),
    # quick activity logging
    path("activities/", api_activities),
    path("activities/log/", api_activity),

    path("login-ui/", login_page, name="login"),
    path("signup-ui/", signup_page, name="signup"),
    path("dashboard/", dashboard_page, name="dashboard"),
    path("chat-ui/", chat_page, name="chat"),
    path("profile-ui/", profile_page, name="profile"),
    path("disease-ui/", disease_page, name="disease"),
]