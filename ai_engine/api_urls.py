from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.api_chat, name='chat_api'),
    path('profile/', views.api_profile, name='get_profile'),
    path('profile/update/', views.api_update_profile, name='update_profile'),
    path('register/', views.api_register, name='register_user'),
    path('chat-history/', views.api_chat_history, name='get_chat_history'),
    path('disease-detection/', views.api_detect, name='detect_disease'),
    path('disease-history/', views.api_history, name='get_disease_history'),
    path('disease-feedback/', views.api_feedback, name='log_treatment_feedback'),
    path('expenses/', views.api_expenses, name='get_expenses'),
    path('expenses/add/', views.api_expense, name='add_expense'),
    path('activities/', views.api_activities, name='get_activities'),
    path('activities/log/', views.api_activity, name='log_activity'),
]