# File: /lesson-plan-generator/backend/lessons/views_separated/payment_views.py

import os
import logging
import requests as http_requests

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from lessons.utils.resolve_profile import resolve_profile
from lessons.models import UserProfile, ManualPaymentProof
from lessons.mtn_service import request_payment

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# PAYMENT PAGE
# ─────────────────────────────────────────────
def payment_page(request):
    plan = (
        request.GET.get('plan')
        or request.session.get('selected_plan')
        or 'monthly'
    )
    valid_plans = ['weekly', 'monthly', 'term']
    if plan not in valid_plans:
        plan = 'monthly'
    request.session['selected_plan'] = plan
    return render(request, 'payment.html', {'selected_plan': plan})


# ─────────────────────────────────────────────
# MTN MOMO — INITIATE PAYMENT
# ─────────────────────────────────────────────
@api_view(['POST'])
def initiate_mtn_payment(request):
    profile = resolve_profile(request)
    plan    = request.data.get('plan')
    phone   = request.data.get('phone')

    if not plan or not phone:
        return Response({'error': 'plan and phone are required'}, status=400)

    plan_prices = {'weekly': 200, 'monthly': 500, 'term': 1000}
    if plan not in plan_prices:
        return Response({'error': 'Invalid plan'}, status=400)

    amount = plan_prices[plan]
    try:
        ref_id = request_payment(amount=amount, phone=phone, external_id=str(profile.id))
    except Exception as e:
        return Response({'error': f'Payment initiation failed: {str(e)}'}, status=500)

    return Response({
        'status':       'PENDING',
        'reference_id': ref_id,
        'amount':       amount,
        'plan':         plan,
    })


# ─────────────────────────────────────────────
# MTN MOMO — CONFIRM PAYMENT
# ─────────────────────────────────────────────
@api_view(['POST'])
def confirm_payment(request):
    profile = resolve_profile(request)
    plan    = request.data.get('plan')

    if not plan:
        return JsonResponse({'status': 'failed', 'error': 'plan is required'}, status=400)

    plan_days_map = {'weekly': 7, 'monthly': 30, 'term': 90}
    days = plan_days_map.get(plan)
    if not days:
        return JsonResponse({'status': 'failed', 'error': 'Invalid plan'}, status=400)

    # ✅ FIX: activate_premium() signature is activate_premium(plan, reset_usage=True)
    # days are handled internally via PLAN_DURATIONS in models.py — do NOT pass days=
    profile.activate_premium(plan=plan, reset_usage=True)
    profile.refresh_from_db()

    return JsonResponse({
        'status':               'success',
        'message':              f"Subscription '{plan}' activated for {days} days.",
        'subscription_expiry':  str(profile.subscription_expiry),  # serialize datetime to string
    })


# ─────────────────────────────────────────────
# SUBSCRIPTION STATUS PAGES
# ─────────────────────────────────────────────
def check_subscription(request):
    return JsonResponse({
        'has_access': False,
        'reason':     'Subscription check not implemented yet',
    })

def subscription_success(request):
    return render(request, 'subscription_success.html')

def subscription_pending(request):
    return render(request, 'subscription_pending.html')


# ═════════════════════════════════════════════
# MANUAL PAYMENT PROOF — INTERNAL HELPERS
# ═════════════════════════════════════════════

def _send_telegram_notification(proof):
    """
    ONE-TIME SETUP:
    1. Telegram → @BotFather → /newbot → copy TOKEN
    2. Create admin group → add bot → send any message
    3. Visit: https://api.telegram.org/bot<TOKEN>/getUpdates
       Find "chat" → "id" (negative number e.g. -1001234567890)
    4. Add to .env.local + Render env vars:
           TELEGRAM_BOT_TOKEN=7xxxxxxxxx:AAxxxxxxx...
           TELEGRAM_CHAT_ID=-1001234567890
    """
    token   = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        logger.warning('Telegram not configured — skipping notification.')
        return False

    plan_prices = {'weekly': '200 RWF', 'monthly': '500 RWF', 'term': '1000 RWF'}
    price       = plan_prices.get(proof.plan, '–')
    admin_url   = (
        f"{os.getenv('SITE_URL', 'https://lesson-plan-generator-va4h.onrender.com')}"
        f"/admin/lessons/manualpaymentproof/{proof.id}/change/"
    )

    message = (
        f"🔔 *New Payment Proof Submitted*\n\n"
        f"👤 *Name:* {proof.full_name}\n"
        f"📱 *Phone:* {proof.phone}\n"
        f"📋 *Plan:* {proof.plan.capitalize()} ({price})\n"
        f"🔑 *Transaction ID:* `{proof.tx_id}`\n"
        f"💰 *Amount Paid:* {proof.amount} RWF\n"
        f"🕐 *Submitted:* {proof.submitted_at.strftime('%d %b %Y %H:%M')} UTC\n"
        f"📧 *User:* {proof.user.email if proof.user else 'Guest'}\n\n"
        f"👉 [Review & Approve in Admin]({admin_url})"
    )

    try:
        resp = http_requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'},
            timeout=10
        )

        if proof.screenshot:
            site_url = os.getenv('SITE_URL', '')
            img_url  = (
                proof.screenshot.url if proof.screenshot.url.startswith('http')
                else f"{site_url}{proof.screenshot.url}"
            )
            http_requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                json={
                    'chat_id': chat_id,
                    'photo':   img_url,
                    'caption': f"📸 Screenshot — {proof.full_name} | Tx: {proof.tx_id}",
                },
                timeout=10
            )

        return resp.status_code == 200

    except Exception as e:
        logger.error(f'Telegram notification failed: {e}')
        return False


def _send_email_notification(proof):
    """
    ONE-TIME SETUP:
    1. Google Account → Security → 2-Step Verification → enable
    2. https://myaccount.google.com/apppasswords → App Password for "Mail"
    3. Add to .env.local + Render env vars:
           EMAIL_HOST_USER=yourgmail@gmail.com
           EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
           ADMIN_EMAIL=yourgmail@gmail.com
    """
    admin_email = os.getenv('ADMIN_EMAIL')
    if not admin_email:
        logger.warning('ADMIN_EMAIL not configured — skipping email.')
        return False

    plan_prices = {'weekly': '200 RWF', 'monthly': '500 RWF', 'term': '1000 RWF'}
    price       = plan_prices.get(proof.plan, '–')
    admin_url   = (
        f"{os.getenv('SITE_URL', 'https://lesson-plan-generator-va4h.onrender.com')}"
        f"/admin/lessons/manualpaymentproof/{proof.id}/change/"
    )

    subject   = f"[CBC App] New Payment Proof — {proof.full_name} ({proof.plan.capitalize()})"
    text_body = (
        f"New payment proof submitted.\n\n"
        f"Name:           {proof.full_name}\n"
        f"Phone:          {proof.phone}\n"
        f"Plan:           {proof.plan.capitalize()} ({price})\n"
        f"Transaction ID: {proof.tx_id}\n"
        f"Amount Paid:    {proof.amount} RWF\n"
        f"Submitted At:   {proof.submitted_at.strftime('%d %b %Y %H:%M')} UTC\n"
        f"User:           {proof.user.email if proof.user else 'Guest'}\n\n"
        f"Review: {admin_url}"
    )
    html_body = f"""
    <html><body style="font-family:Inter,sans-serif;background:#f5f7fa;padding:20px;">
    <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;
                padding:28px;box-shadow:0 4px 15px rgba(0,0,0,0.08);">
        <h2 style="color:#2D9CDB;margin-bottom:4px;">🔔 New Payment Proof</h2>
        <p style="color:#888;font-size:0.9rem;margin-top:0;">CBC Lesson Plan Generator</p>
        <table style="width:100%;border-collapse:collapse;margin-top:16px;">
            <tr><td style="padding:8px 0;color:#555;width:42%;">👤 Full Name</td>
                <td style="padding:8px 0;font-weight:600;">{proof.full_name}</td></tr>
            <tr style="background:#f9f9f9;">
                <td style="padding:8px 0;color:#555;">📱 Phone</td>
                <td style="padding:8px 0;">{proof.phone}</td></tr>
            <tr><td style="padding:8px 0;color:#555;">📋 Plan</td>
                <td style="padding:8px 0;font-weight:600;">{proof.plan.capitalize()} ({price})</td></tr>
            <tr style="background:#f9f9f9;">
                <td style="padding:8px 0;color:#555;">🔑 Transaction ID</td>
                <td style="padding:8px 0;font-family:monospace;">{proof.tx_id}</td></tr>
            <tr><td style="padding:8px 0;color:#555;">💰 Amount Paid</td>
                <td style="padding:8px 0;">{proof.amount} RWF</td></tr>
            <tr style="background:#f9f9f9;">
                <td style="padding:8px 0;color:#555;">📧 User</td>
                <td style="padding:8px 0;">{proof.user.email if proof.user else 'Guest'}</td></tr>
            <tr><td style="padding:8px 0;color:#555;">🕐 Submitted</td>
                <td style="padding:8px 0;">{proof.submitted_at.strftime('%d %b %Y %H:%M')} UTC</td></tr>
        </table>
        <div style="margin-top:22px;text-align:center;">
            <a href="{admin_url}"
               style="background:#2D9CDB;color:#fff;padding:12px 28px;border-radius:25px;
                      text-decoration:none;font-weight:600;">
                ✅ Review & Approve in Admin
            </a>
        </div>
    </div></body></html>
    """

    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.EMAIL_HOST_USER,
            to=[admin_email],
        )
        email.attach_alternative(html_body, 'text/html')

        if proof.screenshot:
            try:
                with proof.screenshot.open('rb') as f:
                    email.attach(
                        proof.screenshot.name.split('/')[-1],
                        f.read(),
                        'image/jpeg'
                    )
            except Exception as e:
                logger.warning(f'Could not attach screenshot: {e}')

        email.send(fail_silently=False)
        return True

    except Exception as e:
        logger.error(f'Email notification failed: {e}')
        return False


# ─────────────────────────────────────────────
# MANUAL PAYMENT — SUBMIT PROOF
# ─────────────────────────────────────────────
@csrf_exempt
def submit_payment_proof(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    full_name = request.POST.get('full_name', '').strip()
    plan      = request.POST.get('plan', 'monthly').strip()

    # Only full_name is required
    if not full_name:
        return JsonResponse(
            {'success': False, 'error': 'Full name is required.'},
            status=400
        )

    if plan not in ('weekly', 'monthly', 'term'):
        plan = 'monthly'

    try:
        proof = ManualPaymentProof.objects.create(
            user      = request.user if request.user.is_authenticated else None,
            full_name = full_name,
            plan      = plan,
            status    = 'pending',
        )
    except Exception as e:
        logger.error(f'Failed to save ManualPaymentProof: {e}')
        return JsonResponse(
            {'success': False, 'error': 'Could not save proof. Please contact admin via WhatsApp.'},
            status=500
        )

    telegram_ok = _send_telegram_notification(proof)
    email_ok    = _send_email_notification(proof)

    logger.info(
        f'Proof #{proof.id} saved | '
        f'Telegram: {"OK" if telegram_ok else "FAIL"} | '
        f'Email: {"OK" if email_ok else "FAIL"}'
    )

    return JsonResponse({
        'success':  True,
        'proof_id': proof.id,
        'telegram': telegram_ok,
        'email':    email_ok,
        'message':  'Proof submitted. Admin has been notified via Telegram & Email.',
    })