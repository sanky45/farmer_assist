import base64
import json
import mimetypes
from .llm import get_llm

# 🌾 LLM Prompt for Disease Detection
DISEASE_DETECTION_PROMPT = """You are an expert agricultural disease detection specialist. Analyze this crop image and provide detailed disease diagnosis.

RESPOND WITH VALID JSON ONLY (no markdown, no extra text):
{
  "disease_detected": "Disease/pest name",
  "confidence": 85,
  "severity": "Mild|Moderate|Severe",
  "severity_description": "% of damage",
  "reason": "Why this occurred",
  "leaf_damage_percentage": 35,
  
  "organic_solutions": [
    {"name": "Neem oil", "dosage": "5ml/liter", "frequency": "Every 7-10 days", "cost": 300, "currency": "INR", "application_time": "Early morning", "duration_days": 14, "local_availability": "Available in shops", "benefits": "Natural"}
  ],
  
  "chemical_solutions": [
    {"name": "Chlorothalonil 75% WP", "dosage": "2.5ml/liter", "frequency": "Every 10-14 days", "cost": 400, "currency": "INR", "application_time": "Early morning", "duration_days": 21, "local_availability": "Available", "precautions": "Use gear", "effectiveness": "95%"}
  ],
  
  "prevention_tips": ["Remove infected leaves", "Improve air circulation", "Use drip irrigation"],
  
  "recovery_timeline": {
    "with_treatment": "7-14 days improvement, 21-30 days full recovery",
    "without_treatment": "Total loss in 45-60 days"
  },
  
  "yield_impact": {
    "if_treated_early": "80-90% recovery",
    "if_untreated": "50-80% loss",
    "financial_impact": "₹15,000-50,000 loss/acre"
  },
  
  "soil_type_consideration": "More severe in clay soils",
  "best_time_to_apply": "Early morning (5-8 AM)",
  "weather_impact": "Thrives in high humidity (>80%)",
  "similar_diseases_ruled_out": ["Late Blight - different pattern"],
  "immediate_action": "Remove infected leaves today"
}
"""


class DiseaseDetectorService:
    """Simple LLM-based disease detector - image → LLM → JSON response."""

    def __init__(self):
        self.llm = get_llm()

    def detect_disease(self, image_path, crop_type=None, user_profile=None):
        """
        Send crop image to LLM for disease detection.
        
        Args:
            image_path: Path to crop image
            crop_type: Optional crop type (e.g., 'tomato')
            user_profile: Optional UserProfile for context
            
        Returns:
            dict: {'success': bool, 'disease_data': {...} or 'error': msg}
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')
            
            mime_type, _ = mimetypes.guess_type(image_path)
            mime_type = mime_type or 'image/jpeg'
            
            # Build context from profile
            context = ""
            if user_profile:
                context = f"Crop: {user_profile.main_crop}, Location: {user_profile.location}, Soil: {user_profile.soil_type}"
            elif crop_type:
                context = f"Crop: {crop_type}"
            
            # Send to LLM with image
            from langchain_core.messages import HumanMessage
            
            prompt = DISEASE_DETECTION_PROMPT
            if context:
                prompt += f"\n\nContext: {context}"
            
            message = HumanMessage(
                content=[
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
                    {"type": "text", "text": prompt}
                ]
            )
            
            response = self.llm.invoke([message])
            response_text = response.content.strip()
            
            # Parse JSON (remove markdown if present)
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            disease_data = json.loads(response_text)
            
            # Add similar cases count from database
            from .models import DiseaseDetection
            similar = DiseaseDetection.objects.filter(
                detected_disease__icontains=disease_data.get('disease_detected', '')
            ).count()
            disease_data['similar_cases_count'] = similar
            
            return {'success': True, 'disease_data': disease_data}
            
        except FileNotFoundError:
            return {'success': False, 'error': f'Image not found: {image_path}'}
        except json.JSONDecodeError as e:
            return {'success': False, 'error': f'Invalid response format: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Error: {str(e)}'}
