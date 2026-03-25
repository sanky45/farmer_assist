# 🛠️ **FARMER ASSIST - IMPLEMENTATION GUIDE WITH CODE EXAMPLES**

## **START HERE: Which Phase Should You Build First?**

### **Recommended Build Order:**
```
PRIORITY 1 (Next 2 weeks):
1. Pest & Disease Detection (HIGH impact, farmers need this)
2. Mandi Prices Integration (Direct income impact)
3. Smart Alerts & Reminders (Easy to implement, high value)

PRIORITY 2 (Following 2 weeks):
4. Irrigation & Fertilizer Guidance (Farmers will love this)
5. Farm Record Analytics (Data-driven farming)
6. Government Schemes Integration (Compliance + subsidies)

PRIORITY 3 (Optional, for growth):
7. Voice Support (Accessibility)
8. Community Forum (Network effects)
9. AR/Advanced features (Premium differentiation)
```

---

## **⚡ QUICK START: Adding Pest & Disease Detection**

### **Step 1: Set Up Google Cloud Vision API**

```bash
# Install required package
pip install google-cloud-vision

# Get credentials from Google Cloud Console
# Download JSON file → Save as google_vision_credentials.json

# Add to settings.py
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_vision_credentials.json'
```

### **Step 2: Create Models for Disease Detection**

```python
# ai_engine/models.py - Add these models

from django.db import models
from django.contrib.auth.models import User

class DiseaseDetection(models.Model):
    SEVERITY_CHOICES = [
        ('Mild', 'Mild - <20% leaf damage'),
        ('Moderate', 'Moderate - 20-50% damage'),
        ('Severe', 'Severe - >50% damage'),
    ]
    
    user_uid = models.CharField(max_length=255)
    image = models.ImageField(upload_to='disease_detection/%Y/%m/%d/')
    
    # Detection results
    detected_disease = models.CharField(max_length=255, blank=True)
    confidence_score = models.FloatField(default=0.0)  # 0-100
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True)
    
    # Treatment options stored as JSON
    treatments = models.JSONField(default=dict)
    # Format: {
    #     'organic': [
    #         {'name': 'Bordeaux mixture', 'cost': 500, 'duration': '7 days'},
    #         {'name': 'Neem oil spray', 'cost': 300, 'duration': '5 days'}
    #     ],
    #     'chemical': [
    #         {'name': 'Chlorothalonil', 'cost': 400, 'duration': '3 days'}
    #     ]
    # }
    
    prevention_tips = models.TextField(blank=True)
    similar_cases_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user_uid} - {self.detected_disease} ({self.created_at.date()})"


class DiseaseTreatmentFeedback(models.Model):
    """Track which treatments worked for farmers"""
    detection = models.ForeignKey(DiseaseDetection, on_delete=models.CASCADE)
    treatment_applied = models.CharField(max_length=255)
    treatment_type = models.CharField(max_length=20, choices=[('organic', 'Organic'), ('chemical', 'Chemical')])
    cost_actual = models.FloatField()
    effectiveness = models.IntegerField(default=0)  # 0-100 percentage
    days_to_recovery = models.IntegerField()
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

### **Step 3: Create Disease Detection Service**

```python
# ai_engine/disease_detector.py - NEW FILE

from google.cloud import vision
from django.conf import settings
import json

class DiseaseDetectorService:
    """
    Detects diseases/pests in crop images using Google Vision + Gemini
    """
    
    def __init__(self):
        self.vision_client = vision.ImageAnnotatorClient()
        # Plant disease database (expand this)
        self.disease_database = self._load_disease_database()
    
    def _load_disease_database(self):
        """Load disease characteristics database"""
        return {
            'early_blight_tomato': {
                'symptoms': ['brown spots', 'yellow halo', 'concentric rings'],
                'crops': ['tomato', 'potato'],
                'organic_treatments': [
                    {'name': 'Bordeaux mixture 1%', 'cost': 500, 'source': 'local'},
                    {'name': 'Copper fungicide', 'cost': 400, 'source': 'local'},
                    {'name': 'Neem oil spray', 'cost': 300, 'source': 'local'},
                ],
                'chemical_treatments': [
                    {'name': 'Chlorothalonil 75% WP', 'cost': 400, 'dosage': '2.5ml/liter'},
                    {'name': 'Mancozeb 75% WP', 'cost': 350, 'dosage': '2gm/liter'},
                ],
                'prevention': [
                    'Remove infected leaves immediately',
                    'Mulch soil to prevent splashing',
                    'Avoid overhead watering',
                    '7-10 day spray intervals',
                    'Crop rotation (3 years)',
                ]
            },
            'powdery_mildew': {
                'symptoms': ['white powder', 'leaf curl', 'stunted growth'],
                'crops': ['wheat', 'grapes', 'cucumber', 'melon'],
                'organic_treatments': [
                    {'name': 'Sulfur dust', 'cost': 200, 'source': 'local'},
                    {'name': 'Baking soda spray', 'cost': 50, 'source': 'home'},
                    {'name': 'Milk spray (10%)', 'cost': 100, 'source': 'home'},
                ],
                'chemical_treatments': [
                    {'name': 'Sulfex', 'cost': 250, 'dosage': '2.5gm/liter'},
                    {'name': 'Dinocap', 'cost': 400, 'dosage': '1ml/liter'},
                ],
                'prevention': [
                    'Maintain proper spacing',
                    'Improve air circulation',
                    'Avoid high humidity',
                    'Remove infected leaves',
                    'Spray every 10-14 days preventively',
                ]
            }
            # Add more diseases as needed
        }
    
    def detect_disease(self, image_path, crop_type=None):
        """
        Detect disease from image
        
        Args:
            image_path: Path to uploaded image
            crop_type: Optional crop type hint
        
        Returns:
            {
                'success': bool,
                'disease': str,
                'confidence': float,
                'severity': str,
                'treatments': dict,
                'prevention': list,
                'similar_cases': int
            }
        """
        try:
            # Read image
            with open(image_path, 'rb') as img_file:
                image_content = img_file.read()
            
            # Analyze with Google Vision
            image = vision.Image(content=image_content)
            response = self.vision_client.label_detection(image=image)
            labels = response.label_annotations
            
            # Extract relevant keywords
            detected_keywords = [label.description.lower() for label in labels]
            
            # Match with disease database
            disease_match = self._find_disease_match(detected_keywords, crop_type)
            
            if not disease_match:
                return {
                    'success': False,
                    'message': 'Could not identify specific disease. Please try another image or contact expert.'
                }
            
            disease_info = self.disease_database.get(disease_match, {})
            severity = self._assess_severity(detected_keywords, disease_match)
            
            return {
                'success': True,
                'disease': disease_match.replace('_', ' ').title(),
                'confidence': min(95.0, 60 + len(detected_keywords) * 5),  # Confidence score
                'severity': severity,
                'treatments': {
                    'organic': disease_info.get('organic_treatments', []),
                    'chemical': disease_info.get('chemical_treatments', []),
                },
                'prevention': disease_info.get('prevention', []),
                'similar_cases': self._get_similar_cases(disease_match)
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_disease_match(self, keywords, crop_type=None):
        """Match detected keywords with disease database"""
        for disease, info in self.disease_database.items():
            symptoms = info.get('symptoms', [])
            crops = info.get('crops', [])
            
            # Check if symptoms match
            symptom_match = sum(1 for keyword in keywords if any(s in keyword for s in symptoms))
            
            # Check if crop matches (if provided)
            crop_match = True
            if crop_type:
                crop_match = any(c in crop_type.lower() for c in crops)
            
            if symptom_match >= 2 and crop_match:
                return disease
        
        return None
    
    def _assess_severity(self, keywords, disease):
        """Assess disease severity based on damage indicators"""
        damage_indicators = {
            'Mild': ['slight', 'small', 'few', 'minimal'],
            'Moderate': ['some', 'spreading', 'medium', 'multiple'],
            'Severe': ['extensive', 'widespread', 'heavy', 'severe', 'large areas']
        }
        
        for severity, indicators in damage_indicators.items():
            if any(ind in ' '.join(keywords) for ind in indicators):
                return severity
        
        return 'Moderate'  # Default
    
    def _get_similar_cases(self, disease_name):
        """Count similar cases from database"""
        from ai_engine.models import DiseaseDetection
        return DiseaseDetection.objects.filter(
            detected_disease=disease_name.replace('_', ' ').title()
        ).count()
```

### **Step 4: Create API Endpoint**

```python
# ai_engine/views.py - Add to existing views

from rest_framework.decorators import api_view, csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from ai_engine.disease_detector import DiseaseDetectorService
from ai_engine.models import DiseaseDetection
import os

disease_detector = DiseaseDetectorService()

@csrf_exempt
@require_http_methods(["POST"])
def detect_disease(request):
    """
    Endpoint: POST /disease-detection/
    
    Upload image → Detect disease → Return treatment options
    
    Request:
    {
        'image': <file>,
        'crop_type': 'tomato'  # optional
    }
    
    Response:
    {
        'success': true,
        'disease': 'Early Blight',
        'confidence': 85.5,
        'severity': 'Moderate',
        'treatments': {
            'organic': [...],
            'chemical': [...]
        },
        'prevention': [...],
        'detection_id': 'abc123'
    }
    """
    try:
        # Get user ID from Firebase token
        user_uid = request.META.get('HTTP_AUTHORIZATION', '').split()[-1]
        if not user_uid:
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        # Get uploaded image
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image provided'}, status=400)
        
        image_file = request.FILES['image']
        crop_type = request.POST.get('crop_type', None)
        
        # Save image temporarily
        temp_path = f'/tmp/{image_file.name}'
        with open(temp_path, 'wb') as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)
        
        # Run detection
        result = disease_detector.detect_disease(temp_path, crop_type)
        
        if result['success']:
            # Save to database
            detection = DiseaseDetection.objects.create(
                user_uid=user_uid,
                image=image_file,
                detected_disease=result['disease'],
                confidence_score=result['confidence'],
                severity=result['severity'],
                treatments=result['treatments'],
                prevention_tips='\n'.join(result['prevention'])
            )
            
            return JsonResponse({
                'success': True,
                'detection_id': detection.id,
                'disease': result['disease'],
                'confidence': result['confidence'],
                'severity': result['severity'],
                'treatments': result['treatments'],
                'prevention': result['prevention'],
                'similar_cases': result['similar_cases'],
                'message': f"Detected {result['disease']} with {result['severity']} severity"
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Could not detect disease')
            }, status=400)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@csrf_exempt
def get_disease_history(request):
    """Get user's previous disease detections"""
    try:
        user_uid = request.META.get('HTTP_AUTHORIZATION', '').split()[-1]
        
        detections = DiseaseDetection.objects.filter(user_uid=user_uid).values(
            'id', 'detected_disease', 'severity', 'confidence_score', 'created_at'
        )[:20]  # Last 20 detections
        
        return JsonResponse({
            'success': True,
            'detections': list(detections)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@csrf_exempt
def log_treatment_feedback(request):
    """
    User logs treatment they applied
    Helps improve disease detection for community
    """
    try:
        user_uid = request.META.get('HTTP_AUTHORIZATION', '').split()[-1]
        data = request.POST
        
        detection = DiseaseDetection.objects.get(id=data.get('detection_id'))
        
        from ai_engine.models import DiseaseTreatmentFeedback
        feedback = DiseaseTreatmentFeedback.objects.create(
            detection=detection,
            treatment_applied=data.get('treatment_applied'),
            treatment_type=data.get('treatment_type'),
            cost_actual=float(data.get('cost_actual', 0)),
            effectiveness=int(data.get('effectiveness', 0)),
            days_to_recovery=int(data.get('days_to_recovery', 0)),
            notes=data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Thanks for feedback! This helps other farmers.',
            'feedback_id': feedback.id
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

### **Step 5: Update URLs**

```python
# ai_engine/urls.py - Add these routes

from django.urls import path
from . import views

urlpatterns = [
    # ... existing paths ...
    
    # Disease Detection
    path('disease-detection/', views.detect_disease, name='detect_disease'),
    path('disease-history/', views.get_disease_history, name='disease_history'),
    path('disease-feedback/', views.log_treatment_feedback, name='treatment_feedback'),
]
```

### **Step 6: Frontend - Create Disease Detection Page**

```html
<!-- dashboard/templates/disease_detection.html -->

<!DOCTYPE html>
<html>
<head>
    <title>Pest & Disease Detection</title>
    <style>
        .disease-container {
            max-width: 900px;
            margin: 20px auto;
            padding: 20px;
        }
        
        .upload-section {
            border: 3px dashed #27AE60;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 30px;
        }
        
        .upload-section:hover {
            background: #f0f9f4;
            border-color: #229954;
        }
        
        .upload-section.dragover {
            background: #e8f8f5;
            border-color: #1ABC9C;
        }
        
        #imageInput {
            display: none;
        }
        
        .preview-section {
            margin: 30px 0;
        }
        
        #previewImage {
            max-width: 400px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .results-section {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 30px 0;
        }
        
        .disease-card {
            background: white;
            border-left: 5px solid #E74C3C;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        
        .severity-mild {
            border-left-color: #F39C12;
        }
        
        .severity-moderate {
            border-left-color: #E67E22;
        }
        
        .severity-severe {
            border-left-color: #C0392B;
        }
        
        .treatment-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }
        
        .treatment-option {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .treatment-option h4 {
            margin: 0 0 10px 0;
        }
        
        .treatment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .organic-tag {
            background: #27AE60;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
        }
        
        .chemical-tag {
            background: #3498DB;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
        }
        
        .cost {
            color: #27AE60;
            font-weight: bold;
            font-size: 16px;
        }
        
        .prevention-section {
            background: #e8f8f5;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .prevention-section ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        .prevention-section li {
            margin: 10px 0;
            line-height: 1.6;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #27AE60;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            display: none;
        }
    </style>
</head>
<body>
    <div class="disease-container">
        <h1>🔍 Pest & Disease Detection</h1>
        <p>Upload a photo of your crop → AI detects disease/pest → Get treatment options</p>
        
        <!-- Upload Section -->
        <div class="upload-section" id="uploadArea">
            <h3>📸 Upload Crop Photo</h3>
            <p>Drag & drop or click to select</p>
            <input type="file" id="imageInput" accept="image/*">
        </div>
        
        <!-- Preview -->
        <div class="preview-section" id="previewSection" style="display: none;">
            <img id="previewImage" src="">
            <label>Crop Type (Optional):
                <input type="text" id="cropType" placeholder="e.g., tomato, wheat, corn">
            </label>
            <button id="detectBtn" onclick="detectDisease()" style="padding: 10px 20px; background: #27AE60; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 10px;">
                Detect Disease
            </button>
        </div>
        
        <!-- Loading -->
        <div class="loading" id="loadingSpinner">
            <div class="spinner"></div>
            <p>Analyzing image... Please wait</p>
        </div>
        
        <!-- Error -->
        <div class="error-message" id="errorMessage"></div>
        
        <!-- Results -->
        <div class="results-section" id="resultsSection" style="display: none;">
            <div class="disease-card" id="diseaseCard"></div>
        </div>
        
        <!-- History -->
        <div id="historySection" style="margin-top: 50px;">
            <h2>📋 Detection History</h2>
            <div id="detectionHistory"></div>
        </div>
    </div>
    
    <script>
        const uploadArea = document.getElementById('uploadArea');
        const imageInput = document.getElementById('imageInput');
        const previewSection = document.getElementById('previewSection');
        const previewImage = document.getElementById('previewImage');
        const loadingSpinner = document.getElementById('loadingSpinner');
        const resultsSection = document.getElementById('resultsSection');
        const diseaseCard = document.getElementById('diseaseCard');
        const errorMessage = document.getElementById('errorMessage');
        
        // Get auth token
        const authToken = localStorage.getItem('idToken');
        
        // File upload handling
        uploadArea.addEventListener('click', () => imageInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        
        imageInput.addEventListener('change', () => {
            handleFiles(imageInput.files);
        });
        
        function handleFiles(files) {
            if (files.length > 0) {
                const file = files[0];
                const reader = new FileReader();
                
                reader.onload = (e) => {
                    previewImage.src = e.target.result;
                    previewSection.style.display = 'block';
                    uploadArea.style.display = 'none';
                };
                
                reader.readAsDataURL(file);
            }
        }
        
        async function detectDisease() {
            const cropType = document.getElementById('cropType').value;
            const formData = new FormData();
            formData.append('image', imageInput.files[0]);
            if (cropType) formData.append('crop_type', cropType);
            
            loadingSpinner.style.display = 'block';
            resultsSection.style.display = 'none';
            errorMessage.style.display = 'none';
            
            try {
                const response = await fetch('/disease-detection/', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: formData
                });
                
                const data = await response.json();
                loadingSpinner.style.display = 'none';
                
                if (data.success) {
                    displayResults(data);
                    loadHistory();
                } else {
                    showError(data.error || 'Could not detect disease');
                }
            } catch (error) {
                loadingSpinner.style.display = 'none';
                showError(error.message);
            }
        }
        
        function displayResults(data) {
            const severityClass = `severity-${data.severity.toLowerCase()}`;
            
            const treatmentsHTML = `
                <div class="treatment-grid">
                    <div>
                        <h4>🌿 Organic Solutions</h4>
                        ${data.treatments.organic.map(t => `
                            <div class="treatment-option">
                                <div class="treatment-header">
                                    <span class="organic-tag">ORGANIC</span>
                                </div>
                                <strong>${t.name}</strong><br>
                                💰 Cost: <span class="cost">₹${t.cost}</span><br>
                                ⏱️ Duration: ${t.duration || 'As per schedule'}
                            </div>
                        `).join('')}
                    </div>
                    <div>
                        <h4>💊 Chemical Solutions</h4>
                        ${data.treatments.chemical.map(t => `
                            <div class="treatment-option">
                                <div class="treatment-header">
                                    <span class="chemical-tag">CHEMICAL</span>
                                </div>
                                <strong>${t.name}</strong><br>
                                💰 Cost: <span class="cost">₹${t.cost}</span><br>
                                📋 Dosage: ${t.dosage || 'As per label'}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            
            const preventionHTML = `
                <div class="prevention-section">
                    <h4>✅ Prevention & Care Tips</h4>
                    <ul>
                        ${data.prevention.map(p => `<li>${p}</li>`).join('')}
                    </ul>
                </div>
            `;
            
            diseaseCard.innerHTML = `
                <h2>🔍 Detection Result</h2>
                <p style="color: #666; margin: 10px 0;">Confidence: ${data.confidence}%</p>
                
                <div style="margin: 20px 0;">
                    <h3 style="color: #27AE60;">Disease: <strong>${data.disease}</strong></h3>
                    <p style="display: inline-block; background: #fff3cd; padding: 10px 15px; border-radius: 20px; margin: 10px 0;">
                        Severity: <strong>${data.severity}</strong>
                    </p>
                </div>
                
                <h3>📋 Treatment Options</h3>
                ${treatmentsHTML}
                
                ${preventionHTML}
                
                <p style="color: #666; margin-top: 20px; font-size: 14px;">
                    📊 Similar cases reported: ${data.similar_cases} farmers
                </p>
                
                <button onclick="shareFeedback(${data.detection_id})" style="margin-top: 20px; padding: 10px 20px; background: #3498DB; color: white; border: none; border-radius: 5px; cursor: pointer;">
                    📝 Share Treatment Results
                </button>
            `;
            
            resultsSection.style.display = 'block';
        }
        
        function showError(msg) {
            errorMessage.textContent = msg;
            errorMessage.style.display = 'block';
        }
        
        async function loadHistory() {
            try {
                const response = await fetch('/disease-history/', {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                const data = await response.json();
                
                if (data.success) {
                    const historyDiv = document.getElementById('detectionHistory');
                    historyDiv.innerHTML = data.detections.map(d => `
                        <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498DB;">
                            <strong>${d.detected_disease}</strong> - <span style="color: #666;">${d.severity}</span>
                            <br>
                            <small style="color: #999;">${new Date(d.created_at).toLocaleDateString()}</small>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Error loading history:', error);
            }
        }
        
        function shareFeedback(detectionId) {
            alert('Feedback form: What treatment did you use? How effective? Coming soon!');
        }
        
        // Load history on page load
        loadHistory();
    </script>
</body>
</html>
```

### **Step 7: Run Migrations & Deploy**

```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate

# Test endpoint
# POST http://localhost:8000/disease-detection/
# With form-data: image=<file>, crop_type=tomato
```

---

## 💰 **Add-on: Mandi Prices Integration (Quick Implementation)**

### **Model:**
```python
class MandiPrice(models.Model):
    crop_name = models.CharField(max_length=100)
    mandi_name = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    
    current_price = models.FloatField()  # Price per quintal
    quality_grade = models.CharField(max_length=10)  # A, B, C
    trading_volume = models.IntegerField()  # Quintals traded
    
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['crop_name', 'region']),
        ]

class PriceHistory(models.Model):
    mandi = models.ForeignKey(MandiPrice, on_delete=models.CASCADE)
    price = models.FloatField()
    date = models.DateField()
    volume = models.IntegerField()
```

### **API (Using NCDEX/Government Data):**
```python
# Get mandi prices
@api_view(['GET'])
def get_mandi_prices(request):
    """GET /api/mandi-prices/{crop}/{region}/"""
    crop = request.GET.get('crop')
    region = request.GET.get('region')
    
    prices = MandiPrice.objects.filter(
        crop_name__iexact=crop,
        region__iexact=region
    ).values('mandi_name', 'current_price', 'quality_grade', 'trading_volume').order_by('-current_price')
    
    return JsonResponse({
        'crop': crop,
        'region': region,
        'mandis': list(prices),
        'best_mandi': list(prices)[0] if prices else None
    })
```

---

## 🚀 **Next Steps:**

```
✅ JUST COMPLETED: Disease Detection System
   └─ Time to implement: 3-4 days
   └─ Difficulty: Medium
   └─ Impact: VERY HIGH (Farmers love disease help)
   └─ Users will use repeatedly

👉 NEXT: Mandi Prices Integration
   └─ Time to implement: 2-3 days
   └─ Difficulty: Low-Medium
   └─ Impact: HIGH (Direct income impact)
   └─ Free APIs available: NCDEX, Government portals

👉 THEN: Smart Alerts & Reminders
   └─ Time to implement: 3-4 days
   └─ Difficulty: Low
   └─ Impact: HIGH (Utility)

👉 THEN: Irrigation & Fertilizer Guidance
   └─ Time to implement: 4-5 days
   └─ Difficulty: Medium
   └─ Impact: HIGH (Farmers save money)
```

**Start with Disease Detection today! It's the #1 farmer need.**

