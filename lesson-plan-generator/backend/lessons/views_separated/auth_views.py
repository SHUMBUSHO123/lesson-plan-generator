from datetime import timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from lessons.utils.resolve_profile import resolve_profile
from lessons.models import UserProfile



# -----------------------------
# Landing & Pricing
# -----------------------------
def landing(request):
    return render(request, 'landing.html')

def pricing(request):
    return render(request, 'pricing.html')


# ===============================
# DEVICE ID VIEW
# ===============================
@api_view(['GET'])
@permission_classes([AllowAny])
def get_logged_in_user_device_id(request):
    profile = getattr(request.user, 'userprofile', None)
    if not request.user.is_authenticated:
        return Response({"device_id": None}, status=200)


# -----------------------------
# Register / Login / Logout
# -----------------------------
@csrf_exempt
def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        incoming_device_id = request.POST.get("device_id")  # optional from client

        if User.objects.filter(username=email).exists():
            return JsonResponse({"error": "Email already registered"}, status=400)

        user = User.objects.create_user(username=email, email=email, password=password)
        profile = None

        if incoming_device_id:
            guest_profile = UserProfile.objects.filter(device_id=incoming_device_id, user__isnull=True).first()
            if guest_profile:
                guest_profile.user = user
                guest_profile.save()
                profile = guest_profile

        if not profile:
            profile = UserProfile.objects.create(
                user=user,
                device_id=incoming_device_id or str(uuid.uuid4())
            )

        login(request, user)
        request.session['device_id'] = profile.device_id
        return redirect("index")

    return render(request, "register.html")


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        incoming_device_id = request.POST.get("device_id")  # optional from client

        user = authenticate(username=email, password=password)
        if not user:
            return render(request, "login.html", {"error": "Invalid credentials"})

        login(request, user)
        profile, created = UserProfile.objects.get_or_create(user=user)

        if incoming_device_id:
            guest_profile = UserProfile.objects.filter(device_id=incoming_device_id, user__isnull=True).first()
            if guest_profile:
                guest_profile.user = user
                guest_profile.save()
                profile = guest_profile

        if not profile.device_id:
            profile.device_id = incoming_device_id or str(uuid.uuid4())
            profile.save()

        request.session['device_id'] = profile.device_id
        return redirect("index")

    return render(request, "login.html")


def logout_user(request):
    logout(request)
    return redirect("landing")


# -----------------------------
# INDEX WITH HYBRID DEVICE + USER
# -----------------------------
@never_cache
def index(request):
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if not profile.device_id:
            profile.device_id = str(uuid.uuid4())
            profile.save()
    else:
        device_id = request.GET.get('device_id') or str(uuid.uuid4())
        profile, _ = UserProfile.objects.get_or_create(
            device_id=device_id,
            defaults={'user': None}
        )
    return render(request, 'index.html', {'profile': profile})
