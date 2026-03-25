
from django.contrib import admin
from .models import ChatMessage, UserProfile, DiseaseDetection, DiseaseTreatmentFeedback, Expense, CropActivity

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user_uid', 'role', 'timestamp']
    search_fields = ['user_uid', 'message']
    ordering = ['-timestamp']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_uid', 'name', 'location', 'main_crop', 'farm_size']
    search_fields = ['user_uid', 'name', 'location']

@admin.register(DiseaseDetection)
class DiseaseDetectionAdmin(admin.ModelAdmin):
    list_display = ['user_uid', 'detected_disease', 'severity', 'confidence_score', 'created_at']
    search_fields = ['user_uid', 'detected_disease']
    ordering = ['-created_at']

@admin.register(DiseaseTreatmentFeedback)
class DiseaseTreatmentFeedbackAdmin(admin.ModelAdmin):
    list_display = ['detection', 'treatment_type', 'effectiveness', 'days_to_recovery', 'created_at']
    ordering = ['-created_at']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['user_uid', 'date', 'category', 'amount']
    search_fields = ['user_uid', 'category']
    ordering = ['-date']

@admin.register(CropActivity)
class CropActivityAdmin(admin.ModelAdmin):
    list_display = ['user_uid', 'activity_type', 'crop_name', 'date']
    search_fields = ['user_uid', 'crop_name']
    ordering = ['-date']
