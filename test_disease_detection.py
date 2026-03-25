#!/usr/bin/env python
"""
Test script to verify the new LLM-based disease detection system.
Run this to test the disease detection with a sample image.
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from ai_engine.disease_detector import DiseaseDetectorService
from ai_engine.models import UserProfile

def test_disease_detection():
    """Test the disease detection with a sample image"""
    
    print("🌾 Testing LLM-Based Disease Detection System\n")
    
    # Initialize detector
    detector = DiseaseDetectorService()
    print("✅ Detector initialized successfully")
    print(f"   - Using Gemini LLM for analysis")
    print(f"   - Vision capability enabled\n")
    
    # Check if test image exists
    test_image_path = "test.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        print("   Please provide a crop image named 'test.jpg' in the project root")
        print("   Then run this test script again.\n")
        return
    
    print(f"📸 Found test image: {test_image_path}")
    
    # Create a test user profile
    test_profile = UserProfile(
        user_uid="test_user_123",
        name="Test Farmer",
        location="Punjab",
        main_crop="Tomato",
        farm_size="10 acres",
        soil_type="Loamy"
    )
    
    print(f"👨‍🌾 Test farmer profile:")
    print(f"   - Crop: {test_profile.main_crop}")
    print(f"   - Location: {test_profile.location}")
    print(f"   - Soil: {test_profile.soil_type}\n")
    
    # Perform disease detection
    print("🔍 Analyzing image for disease detection...")
    result = detector.detect_disease(
        image_path=test_image_path,
        crop_type=test_profile.main_crop,
        user_profile=test_profile
    )
    
    # Display results
    if result.get('success'):
        print("✅ Disease detection successful!\n")
        disease_data = result.get('disease_data', {})
        
        print("=" * 60)
        print("📋 DISEASE DETECTION RESULTS")
        print("=" * 60)
        
        print(f"\n🦠 Disease: {disease_data.get('disease_detected')}")
        print(f"📊 Confidence: {disease_data.get('confidence')}%")
        print(f"⚠️  Severity: {disease_data.get('severity')}")
        print(f"📈 Leaf Damage: {disease_data.get('leaf_damage_percentage')}%")
        
        print(f"\n💡 Reason: {disease_data.get('reason')}")
        
        print("\n🌿 ORGANIC SOLUTIONS:")
        for i, solution in enumerate(disease_data.get('organic_solutions', []), 1):
            print(f"  {i}. {solution.get('name')}")
            print(f"     Cost: ₹{solution.get('cost')}")
            print(f"     Dosage: {solution.get('dosage')}")
            print(f"     Frequency: {solution.get('frequency')}")
            print(f"     Timeline: {solution.get('duration_days')} days")
        
        print("\n💊 CHEMICAL SOLUTIONS:")
        for i, solution in enumerate(disease_data.get('chemical_solutions', []), 1):
            print(f"  {i}. {solution.get('name')}")
            print(f"     Cost: ₹{solution.get('cost')}")
            print(f"     Effectiveness: {solution.get('effectiveness')}")
            print(f"     Duration: {solution.get('duration_days')} days")
        
        print("\n📅 RECOVERY TIMELINE:")
        timeline = disease_data.get('recovery_timeline', {})
        print(f"  With treatment: {timeline.get('with_treatment')}")
        print(f"  Without treatment: {timeline.get('without_treatment')}")
        
        print("\n💰 FINANCIAL IMPACT:")
        impact = disease_data.get('yield_impact', {})
        print(f"  If treated: {impact.get('if_treated_early')}")
        print(f"  If untreated: {impact.get('if_untreated')}")
        print(f"  Loss estimate: {impact.get('financial_impact')}")
        
        print("\n🌱 SOIL CONSIDERATION:")
        print(f"  {disease_data.get('soil_type_consideration')}")
        
        print("\n⏰ BEST TIME TO APPLY:")
        print(f"  {disease_data.get('best_time_to_apply')}")
        
        print("\n🌦️  WEATHER IMPACT:")
        print(f"  {disease_data.get('weather_impact')}")
        
        print("\n✅ PREVENTION TIPS:")
        for i, tip in enumerate(disease_data.get('prevention_tips', []), 1):
            print(f"  {i}. {tip}")
        
        print("\n🚨 IMMEDIATE ACTION:")
        print(f"  {disease_data.get('immediate_action')}")
        
        print("\n" + "=" * 60)
        print("✅ Disease detection API is working correctly!")
        print("=" * 60)
        
    else:
        print(f"❌ Disease detection failed!")
        print(f"   Error: {result.get('error')}")
        if result.get('raw_response'):
            print(f"   Raw Response: {result.get('raw_response')}")

if __name__ == "__main__":
    test_disease_detection()
