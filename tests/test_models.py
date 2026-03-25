import pytest
from django.test import TestCase
from ai_engine.models import UserProfile, ChatMessage, DiseaseDetection


@pytest.mark.unit
class UserProfileModelTest(TestCase):
    def test_user_profile_creation(self):
        """Test that UserProfile can be created"""
        profile = UserProfile.objects.create(
            user_uid="test_uid",
            name="Test User",
            location="Test Location",
            main_crop="Rice",
            farm_size=5.0,
            soil_type="Clay"
        )
        self.assertEqual(profile.name, "Test User")
        self.assertEqual(profile.main_crop, "Rice")


@pytest.mark.unit
class ChatMessageModelTest(TestCase):
    def test_chat_message_creation(self):
        """Test that ChatMessage can be created"""
        message = ChatMessage.objects.create(
            user_uid="test_uid",
            role="user",
            message="Hello AI"
        )
        self.assertEqual(message.role, "user")
        self.assertEqual(message.message, "Hello AI")


@pytest.mark.unit
class DiseaseDetectionModelTest(TestCase):
    def test_disease_detection_creation(self):
        """Test that DiseaseDetection can be created"""
        detection = DiseaseDetection.objects.create(
            user_uid="test_uid",
            image="test_image.jpg",
            detected_disease="Leaf Blight",
            confidence_score=85,
            severity="Moderate"
        )
        self.assertEqual(detection.detected_disease, "Leaf Blight")
        self.assertEqual(detection.confidence_score, 85)