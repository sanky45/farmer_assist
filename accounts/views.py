# Create your views here.
from django.http import JsonResponse
from .utils import verify_firebase_token
from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def firebase_login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        # Parse JSON safely
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        
        id_token = data.get("idToken")

        if not id_token:
            return JsonResponse({"error": "idToken is required"}, status=400)

        decoded = verify_firebase_token(id_token)

        if decoded:
            return JsonResponse({
                "status": "success",
                "uid": decoded["uid"],
                "email": decoded.get("email", ""),
                "name": decoded.get("name", "")
            })
        else:
            return JsonResponse({"status": "invalid token", "error": "Token verification failed"}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Login error: {str(e)}"}, status=500)