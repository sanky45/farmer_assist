from django.db import models

# Create your models here.
from django.db import models


class ChatMessage(models.Model):
    user_uid = models.CharField(max_length=255)
    role = models.CharField(max_length=20)  # "user" or "assistant"
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_uid} - {self.role}"
    



class UserProfile(models.Model):
    user_uid = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    main_crop = models.CharField(max_length=100, blank=True, null=True)
    farm_size = models.CharField(max_length=100, blank=True, null=True)
    soil_type = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_uid


class DiseaseDetection(models.Model):
    """Stores results of crop image disease/pest analysis"""
    SEVERITY_CHOICES = [
        ('Mild', 'Mild - <20% leaf damage'),
        ('Moderate', 'Moderate - 50% damage'),
        ('Severe', 'Severe - >50% damage'),
    ]

    user_uid = models.CharField(max_length=255)
    image = models.ImageField(upload_to='disease_detection/%Y/%m/%d/')
    detected_disease = models.CharField(max_length=255, blank=True)
    confidence_score = models.FloatField(default=0.0)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True)
    treatments = models.JSONField(default=dict)
    prevention_tips = models.TextField(blank=True)
    similar_cases_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_uid} - {self.detected_disease} ({self.created_at.date()})"


class DiseaseTreatmentFeedback(models.Model):
    """Log feedback from farmers on treatments they applied"""
    detection = models.ForeignKey(DiseaseDetection, on_delete=models.CASCADE)
    treatment_applied = models.CharField(max_length=255)
    treatment_type = models.CharField(max_length=20, choices=[('organic','Organic'),('chemical','Chemical')])
    cost_actual = models.FloatField()
    effectiveness = models.IntegerField(default=0)  # 0-100%
    days_to_recovery = models.IntegerField()
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class Expense(models.Model):
    """Tracks an individual farming expense"""
    CATEGORY_CHOICES = [
        ('water', 'Water'),
        ('fertilizer', 'Fertilizer'),
        ('labor', 'Labor'),
        ('other', 'Other'),
    ]

    user_uid = models.CharField(max_length=255)
    date = models.DateField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.FloatField()
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user_uid} - {self.category} ₹{self.amount} on {self.date}"


class CropActivity(models.Model):
    """Quick log of field activities like watering/fertilizing"""
    ACTIVITY_CHOICES = [
        ('water', 'Watering'),
        ('fertilizer', 'Fertilizer application'),
    ]

    user_uid = models.CharField(max_length=255)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    crop_name = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField()
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user_uid} - {self.activity_type} ({self.crop_name}) on {self.date}"

