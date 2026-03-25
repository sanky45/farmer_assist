import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from accounts.utils import verify_firebase_token
from .agent import run_agent
from .models import ChatMessage, UserProfile, DiseaseDetection, DiseaseTreatmentFeedback, Expense, CropActivity


# ------------------------------------------------------------------
# simple page views for rendering templates
# ------------------------------------------------------------------

def login_page(request):
    return render(request, "login.html")


def signup_page(request):
    return render(request, "signup.html")


def dashboard_page(request):
    return render(request, "dashboard.html")


def chat_page(request):
    return render(request, "chat.html")


def profile_page(request):
    return render(request, "profile.html")


def disease_page(request):
    return render(request, "disease_detection.html")


from .disease_detector import DiseaseDetectorService

detector = DiseaseDetectorService()


@csrf_exempt
def api_register(request):
    """Register or update user profile after Firebase signup"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_firebase_token(id_token)

    if not decoded_token:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        user_uid = decoded_token["uid"]

        # Create or update profile
        profile, created = UserProfile.objects.get_or_create(user_uid=user_uid)

        profile.name = data.get("name", profile.name)
        profile.location = data.get("location", profile.location)
        profile.main_crop = data.get("main_crop", profile.main_crop)
        profile.farm_size = data.get("farm_size", profile.farm_size)
        profile.soil_type = data.get("soil_type", profile.soil_type)

        profile.save()

        return JsonResponse({
            "message": "User registered successfully",
            "profile": {
                "name": profile.name,
                "location": profile.location,
                "main_crop": profile.main_crop,
                "farm_size": profile.farm_size,
                "soil_type": profile.soil_type,
            }
        })

    except Exception as e:
        return JsonResponse({"error": f"Registration error: {str(e)}"}, status=500)


@csrf_exempt
def api_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    # 🔐 Get Authorization header
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_firebase_token(id_token)

    if not decoded_token:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        # Parse JSON body safely
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        
        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"error": "Message is required and cannot be empty"}, status=400)
        
        if len(user_message) > 5000:
            return JsonResponse({"error": "Message is too long (max 5000 characters)"}, status=400)

        user_uid = decoded_token["uid"]

        # 🧱 Ensure User Profile Exists
        profile, _ = UserProfile.objects.get_or_create(
            user_uid=user_uid
        )

        # 🧠 1️⃣ Get last 10 messages (latest first)
        chat_history = ChatMessage.objects.filter(
            user_uid=user_uid
        ).order_by("-timestamp")[:10]

        # 🔁 Reverse so oldest comes first
        chat_history = list(reversed(chat_history))

        # 🧠 2️⃣ Run AI Agent with memory + profile
        try:
            ai_response = run_agent(user_message, chat_history, profile)
        except Exception as e:
            return JsonResponse({"error": f"AI Agent error: {str(e)}"}, status=500)

        # ensure response is string before returning/saving
        ai_response = str(ai_response)

        # 💾 3️⃣ Save user message
        ChatMessage.objects.create(
            user_uid=user_uid,
            role="user",
            message=user_message
        )

        # 💾 4️⃣ Save AI response
        ChatMessage.objects.create(
            user_uid=user_uid,
            role="assistant",
            message=ai_response
        )

        return JsonResponse({
            "response": ai_response
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




# ------------------------------------------------
# �🚜 Pest & Disease Detection APIs
# ------------------------------------------------

@csrf_exempt
def api_detect(request):
    """Handle POST image upload and return AI-powered diagnosis"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)
    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_firebase_token(id_token)
    if not decoded:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        if 'image' not in request.FILES:
            return JsonResponse({"error": "No image provided"}, status=400)
        image_file = request.FILES['image']
        crop_type = request.POST.get('crop_type', None)

        # temporarily save file
        temp_path = f"/tmp/{image_file.name}"
        with open(temp_path, 'wb') as tmp:
            for chunk in image_file.chunks():
                tmp.write(chunk)

        # Get user profile for context
        user_uid = decoded['uid']
        user_profile = UserProfile.objects.filter(user_uid=user_uid).first()

        # Analyze image using LLM
        result = detector.detect_disease(temp_path, crop_type, user_profile)
        
        if result.get('success'):
            # Extract disease data from LLM response
            disease_data = result.get('disease_data', {})
            disease_name = disease_data.get('disease_detected', 'Unknown Disease')
            confidence = disease_data.get('confidence', 75)
            severity = disease_data.get('severity', 'Moderate')
            
            # record detection in database
            detection = DiseaseDetection.objects.create(
                user_uid=user_uid,
                image=image_file,
                detected_disease=disease_name,
                confidence_score=float(confidence),
                severity=severity,
                treatments=json.dumps({
                    'organic': disease_data.get('organic_solutions', []),
                    'chemical': disease_data.get('chemical_solutions', [])
                }),
                prevention_tips='\n'.join(disease_data.get('prevention_tips', []))
            )
            
            return JsonResponse({
                'success': True,
                'detection_id': detection.id,
                'disease_data': disease_data
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Disease detection failed')
            }, status=400)
            
    except Exception as e:
        print(f"[detect_disease] error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)



@csrf_exempt
def api_history(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)
    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_firebase_token(id_token)
    if not decoded:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        detections = DiseaseDetection.objects.filter(user_uid=decoded['uid']).values(
            'id','detected_disease','severity','confidence_score','created_at'
        )[:20]
        return JsonResponse({'success': True, 'detections': list(detections)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# -------------------------
# 💰 Expense tracking APIs
# -------------------------

@csrf_exempt
def api_activity(request):
    """Quick log for watering/fertilizer actions"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)
    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_firebase_token(id_token)
    if not decoded:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        # required fields
        activity_type = data.get('activity_type')
        if activity_type not in ('water', 'fertilizer'):
            return JsonResponse({"error": "Invalid activity type"}, status=400)

        date_str = data.get('date')
        if not date_str:
            return JsonResponse({"error": "Date is required"}, status=400)
        
        crop_name = data.get('crop_name', '')
        notes = data.get('notes', '')

        activity = CropActivity.objects.create(
            user_uid=decoded['uid'],
            activity_type=activity_type,
            crop_name=crop_name,
            date=date_str,  # Django will auto-convert YYYY-MM-DD string to date
            notes=notes
        )
        return JsonResponse({"success": True, "activity_id": activity.id})
    except Exception as e:
        print("[log_activity] error:", str(e))
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt

def api_expense(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)
    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_firebase_token(id_token)
    if not decoded:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        expense = Expense.objects.create(
            user_uid=decoded['uid'],
            date=data.get('date'),
            category=data.get('category', 'other'),
            amount=float(data.get('amount', 0)),
            description=data.get('description', '')
        )
        return JsonResponse({"success": True, "expense_id": expense.id})
    except Exception as e:
        # log exception on server for debugging
        print("[add_expense] error:", e)
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_expenses(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)
    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_firebase_token(id_token)
    if not decoded:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        expenses = Expense.objects.filter(user_uid=decoded['uid']).values('date','category','amount','description')
        # fetch farm size to help frontend
        profile = UserProfile.objects.filter(user_uid=decoded['uid']).first()
        farm_size = profile.farm_size if profile else None
        return JsonResponse({"success": True, "expenses": list(expenses), "farm_size": farm_size})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
    
def api_activities(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)
    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_firebase_token(id_token)
    if not decoded:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)
    try:
        activities = CropActivity.objects.filter(user_uid=decoded['uid']).values('date','activity_type','crop_name','notes')[:50]
        return JsonResponse({"success": True, "activities": list(activities)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_feedback(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)
    id_token = auth_header.split("Bearer ")[1]
    decoded = verify_firebase_token(id_token)
    if not decoded:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)
    try:
        data = request.POST
        detection = DiseaseDetection.objects.get(id=data.get('detection_id'))
        feedback = DiseaseTreatmentFeedback.objects.create(
            detection=detection,
            treatment_applied=data.get('treatment_applied'),
            treatment_type=data.get('treatment_type'),
            cost_actual=float(data.get('cost_actual',0)),
            effectiveness=int(data.get('effectiveness',0)),
            days_to_recovery=int(data.get('days_to_recovery',0)),
            notes=data.get('notes','')
        )
        return JsonResponse({'success': True, 'feedback_id': feedback.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    


@csrf_exempt
def api_profile(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_firebase_token(id_token)

    if not decoded_token:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    user_uid = decoded_token["uid"]

    try:
        profile = UserProfile.objects.get(user_uid=user_uid)

        return JsonResponse({
            "name": profile.name,
            "location": profile.location,
            "main_crop": profile.main_crop,
            "farm_size": profile.farm_size,
            "soil_type": profile.soil_type,
        })

    except UserProfile.DoesNotExist:
        # Return empty profile for new users
        return JsonResponse({
            "name": None,
            "location": None,
            "main_crop": None,
            "farm_size": None,
            "soil_type": None,
            "message": "Profile not found. Create one by updating."
        }, status=200)
    except Exception as e:
        return JsonResponse({"error": f"Error retrieving profile: {str(e)}"}, status=500)


@csrf_exempt
def api_update_profile(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_firebase_token(id_token)

    if not decoded_token:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    user_uid = decoded_token["uid"]

    try:
        # Parse JSON body safely
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        profile, _ = UserProfile.objects.get_or_create(user_uid=user_uid)

        profile.name = data.get("name", profile.name)
        profile.location = data.get("location", profile.location)
        profile.main_crop = data.get("main_crop", profile.main_crop)
        profile.farm_size = data.get("farm_size", profile.farm_size)
        profile.soil_type = data.get("soil_type", profile.soil_type)

        profile.save()

        return JsonResponse({
            "message": "Profile updated successfully",
            "profile": {
                "name": profile.name,
                "location": profile.location,
                "main_crop": profile.main_crop,
                "farm_size": profile.farm_size,
                "soil_type": profile.soil_type,
            }
        })

    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "Profile not found"}, status=404)


@csrf_exempt
def api_chat_history(request):
    """Get user's chat history"""
    if request.method != "GET":
        return JsonResponse({"error": "Only GET method allowed"}, status=405)

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Authorization token required"}, status=401)

    id_token = auth_header.split("Bearer ")[1]
    decoded_token = verify_firebase_token(id_token)

    if not decoded_token:
        return JsonResponse({"error": "Invalid or expired token"}, status=401)

    try:
        user_uid = decoded_token["uid"]
        
        # Get all messages for this user, ordered by timestamp (newest first)
        messages = ChatMessage.objects.filter(
            user_uid=user_uid
        ).order_by("-timestamp").values("message", "role", "timestamp")

        # Convert to list and reverse to get oldest first
        messages_list = list(messages)
        messages_list.reverse()

        return JsonResponse(messages_list, safe=False)

    except Exception as e:
        return JsonResponse({"error": f"Error retrieving chat history: {str(e)}"}, status=500)


