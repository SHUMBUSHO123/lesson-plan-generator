from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from lessons.utils.resolve_profile import resolve_profile
from lessons.models import UserProfile
from lessons.mtn_service import request_payment
from django.http import JsonResponse
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
import json


def payment_page(request):
    return render(request, "payment.html")


@api_view(['POST'])
def initiate_mtn_payment(request):
    profile = resolve_profile(request)
    plan = request.data.get("plan")
    phone = request.data.get("phone")

    if not plan or not phone:
        return Response({"error": "plan and phone are required"}, status=400)

    plan_prices = {"weekly": 20, "monthly": 50, "term": 111}
    if plan not in plan_prices:
        return Response({"error": "Invalid plan"}, status=400)

    amount = plan_prices[plan]

    try:
        ref_id = request_payment(amount=amount, phone=phone, external_id=str(profile.id))
    except Exception as e:
        return Response({"error": f"Payment initiation failed: {str(e)}"}, status=500)

    return Response({"status": "PENDING", "reference_id": ref_id, "amount": amount, "plan": plan})


@api_view(['POST'])
def confirm_payment(request):
    profile = resolve_profile(request)
    plan = request.data.get("plan")
    if not plan:
        return JsonResponse({"status": "failed", "error": "plan is required"}, status=400)

    plan_days_map = {"weekly": 7, "monthly": 30, "term": 90}
    days = plan_days_map.get(plan)
    if not days:
        return JsonResponse({"status": "failed", "error": "Invalid plan"}, status=400)

    profile.activate_premium(plan=plan, days=days, reset_usage=True)
    return JsonResponse({"status": "success", "message": f"Subscription '{plan}' activated for {days} days.", "subscription_expiry": profile.subscription_expiry})


def check_subscription(request):
    return JsonResponse({
        "has_access": False,
        "reason": "Subscription check not implemented yet"
    })

def subscription_success(request):
    return render(request, "subscription_success.html")


@csrf_exempt
@api_view(['POST'])
def submit_manual_payment(request):
    try:
        data = json.loads(request.body)
        code = data.get("code")
        plan = data.get("plan")
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid data"}, status=400)

    if not code or not plan:
        return JsonResponse({"success": False, "error": "Code and plan are required"}, status=400)

    # Here you can add your real manual verification logic
    # For now, we'll just simulate acceptance
    return JsonResponse({"success": True, "message": "Manual payment submitted. Await admin approval."})

def subscription_pending(request):
    return render(request, "subscription_pending.html")
