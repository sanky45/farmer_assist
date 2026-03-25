import firebase_admin
from firebase_admin import credentials
import os

# Prevent multiple initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_service_account.json")
    firebase_admin.initialize_app(cred)