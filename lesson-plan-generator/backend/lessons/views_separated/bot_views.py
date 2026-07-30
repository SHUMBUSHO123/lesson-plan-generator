# File: /lesson-plan-generator/backend/lessons/views_separated/bot_views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
import json
import re
import logging
from lessons.models import BotResponse

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def chat_bot_api(request):
    """
    Main chatbot API endpoint - FULL BACKEND CONTROL
    Everything here can be changed without touching JavaScript!
    """
    
    try:
        # Parse request
        data = json.loads(request.body)
        user_message = data.get('message', '').lower().strip()
        conversation_id = data.get('conversation_id', '')
        user_language = data.get('language', 'en')
        
        # Get user data (if logged in)
        user = request.user if request.user.is_authenticated else None
        
        # ========================================
        # 1. USER DATA (FULL CONTROL)
        # ========================================
        user_data = {
            'is_authenticated': user is not None,
            'username': user.username if user else None,
            'email': user.email if user else None,
            'user_id': user.id if user else None,
        }
        
        # ========================================
        # 2. SUBSCRIPTION DATA (FULL CONTROL)
        # ========================================
        subscription_data = {
            'plan': 'free',
            'is_premium': False,
            'lessons_used': 0,
            'lessons_remaining': 3,
            'expiry_date': None,
            'can_download_pdf': False,
            'can_download_docx': False,
        }
        
        if user:
            # Check if user has subscription model
            if hasattr(user, 'subscription') and user.subscription:
                sub = user.subscription
                subscription_data = {
                    'plan': getattr(sub, 'plan_name', 'free'),
                    'is_premium': getattr(sub, 'plan_name', 'free') in ['monthly', 'term', 'premium'],
                    'lessons_used': getattr(sub, 'lessons_generated', 0),
                    'lessons_remaining': getattr(sub, 'remaining_lessons', 3) if not getattr(sub, 'is_premium', False) else 'unlimited',
                    'expiry_date': getattr(sub, 'expiry_date', None),
                    'can_download_pdf': getattr(sub, 'plan_name', 'free') != 'free',
                    'can_download_docx': getattr(sub, 'plan_name', 'free') in ['monthly', 'term'],
                }
            else:
                # Fallback: check UserProfile if exists
                if hasattr(user, 'userprofile'):
                    profile = user.userprofile
                    subscription_data['lessons_used'] = getattr(profile, 'lessons_generated', 0)
                    subscription_data['lessons_remaining'] = max(0, 3 - subscription_data['lessons_used'])
        
        # ========================================
        # 3. INTENT DETECTION (UPDATE ANYTIME)
        # ========================================
        intent = detect_intent(user_message)
        
        # ========================================
        # 4. RESPONSE GENERATION (UPDATE ANYTIME)
        # ========================================
        response = generate_bot_response(
            intent=intent,
            user_message=user_message,
            user_data=user_data,
            subscription_data=subscription_data,
            language=user_language
        )
        
        # ========================================
        # 5. FOLLOW-UP SUGGESTIONS
        # ========================================
        suggestions = get_suggestions(intent, subscription_data['is_premium'])
        
        # ========================================
        # 6. QUICK ACTIONS (Buttons to show)
        # ========================================
        quick_actions = get_quick_actions(intent, user_data['is_authenticated'])
        
        # ========================================
        # 7. SAVE CONVERSATION (Optional)
        # ========================================
        if user and conversation_id:
            save_conversation(user, conversation_id, user_message, response, intent)
        
        # ========================================
        # 8. RETURN RESPONSE
        # ========================================
        return JsonResponse({
            'success': True,
            'response': response,
            'intent': intent,
            'suggestions': suggestions,
            'quick_actions': quick_actions,
            'user_status': {
                'is_authenticated': user_data['is_authenticated'],
                'is_premium': subscription_data['is_premium'],
                'plan': subscription_data['plan'],
                'lessons_remaining': subscription_data['lessons_remaining']
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return JsonResponse({'error': 'Server error'}, status=500)


def detect_intent(message):
    """
    Detect user intent - FULL CONTROL
    Update keywords anytime without redeploying JS
    """
    message_lower = message.lower()
    
    # Intent definitions - ORDER MATTERS! Put more specific intents FIRST
    intents = {
        # Payment issues - most specific, check first
        'payment_issue': [
            'payment deducted', 'not activated', 'money deducted', 'paid but', 
            'already paid', 'payment not', 'charged but', 'activation issue',
            'payment problem', 'transaction failed', 'deducted but'
        ],
        # Contact admin - direct support request
        'contact_admin': [
            'admin', 'speak to admin', 'talk to admin', 'contact support',
            'help desk', 'human support', 'speak to manager', 'talk to human'
        ],
        # Troubleshoot - technical issues
        'troubleshoot': [
            'error', 'bug', 'not working', 'technical issue', 'problem', 
            'broken', 'failing', 'doesn\'t work', 'issue with'
        ],
        # Account status - check subscription
        'account_status': [
            'my status', 'account status', 'check my plan', 'remaining lessons',
            'what plan', 'am i premium', 'subscription status', 'how many left'
        ],
        # Generate lesson - main feature
        'generate_lesson': [
            'generate', 'lesson plan', 'create lesson', 'make plan', 'new plan',
            'how to generate', 'create plan', 'make lesson'
        ],
        # Pricing - subscription plans
        'pricing': [
            'price', 'cost', 'subscription', 'upgrade', 'premium', 'pay',
            'payment', 'plan', 'subscribe', 'how much', 'rwf', 'fees', 'pricing'
        ],
        # Download - export options
        'download': [
            'download', 'export', 'pdf', 'docx', 'word', 'save', 'print',
            'get my plan', 'copy to word'
        ],
        # Create account - registration
        'create_account': [
            'create account', 'register', 'sign up', 'new account',
            'how to register', 'create free account'
        ],
        # Login - authentication
        'login': [
            'login', 'sign in', 'log in', 'access account', 'can\'t login'
        ],
        # Forgot password - reset
        'forgot_password': [
            'forgot password', 'reset password', 'password reset', 'change password'
        ],
        # Help - general assistance
        'help': [
            'help', 'assist', 'guide', 'tutorial', 'what can you do',
            'capabilities', 'how to use'
        ],
        # Greeting - welcome messages
        'greeting': [
            'hi', 'hello', 'hey', 'muraho', 'sasa', 'good morning',
            'good afternoon', 'hola', 'howdy'
        ],
        # Thanks - appreciation
        'thanks': [
            'thank', 'thanks', 'appreciate', 'grateful', 'awesome', 'great',
            'perfect', 'amazing'
        ],
        # Goodbye - exit
        'goodbye': [
            'bye', 'goodbye', 'see you', 'later', 'exit', 'quit', 'cya'
        ],
    }
    
    # Check for intent matches
    for intent, keywords in intents.items():
        for keyword in keywords:
            if keyword in message_lower:
                print(f"Intent detected: {intent} (keyword: {keyword})")
                return intent
    
    print(f"No intent detected, returning default for: {message_lower}")
    return 'default'

def generate_bot_response(intent, user_message, user_data, subscription_data, language='en'):
    """
    Generate bot response - PRIORITIZES DATABASE, falls back to hardcoded
    """
    
    is_authenticated = user_data['is_authenticated']
    is_premium = subscription_data['is_premium']
    username = user_data['username'] or 'there'
    remaining = subscription_data['lessons_remaining']
    email = user_data['email'] or ''
    
    print(f"Generating response for intent: {intent}")  # Debug log
    
    # ========================================
    # FIRST: Try to get response from DATABASE
    # ========================================
    try:
        from lessons.models import BotResponse
        bot_response = BotResponse.objects.filter(
            intent=intent, 
            is_active=True
        ).order_by('priority').first()
        
        if bot_response:
            print(f"✅ Using DATABASE response for intent: {intent}")
            # Format the response with variables
            response = bot_response.response_template.format(
                username=username,
                remaining=remaining,
                email=email,
                plan=subscription_data.get('plan', 'free'),
                is_premium=is_premium,
                is_authenticated=is_authenticated
            )
            return response
    except Exception as e:
        print(f"⚠️ Error loading bot response from DB: {e}")
    
    # ========================================
    # SECOND: Fallback to hardcoded responses
    # ========================================
    print(f"📝 Using HARDCODED fallback for intent: {intent}")
    
    if intent == 'greeting':
        if is_authenticated:
            return f"👋 **Hello {username}!** Welcome back to IsomoPlus!\n\nHow can I help you today?\n\n📝 Generate a lesson plan\n💰 Check pricing\n📥 Download your plan"
        else:
            return "👋 **Hello! Welcome to IsomoPlus!**\n\nI'm your AI assistant.\n\n🔓 **I see you're not registered yet.**\n\n👉 Create a free account for 3 lesson plans\n👉 Login if you already have an account\n\nWhat would you like to know?"
    
    if intent == 'generate_lesson':
        if is_authenticated:
            return "📝 **To generate a lesson plan:**\n\n1. Fill in the school name and teacher's name\n2. Select your class, subject, and unit\n3. Click '✨ Generate Lesson Plan'\n\nWould you like help with any specific field?"
        else:
            return "📝 **To generate a lesson plan, you need an account!**\n\n🔗 **Register here:** /register/\n\nIt's free and gives you 3 lesson plans to start!"
    
    if intent == 'pricing':
        return "💰 **IsomoPlus Subscription Plans:**\n\n📅 **Weekly** - RWF 500\n📆 **Monthly** - RWF 1500 ⭐ **Best Value!**\n📚 **Term** - RWF 3500\n\n**Free Plan:** 3 lesson plans to try!\n\n🔗 **Subscribe:** /pricing/\n\nWould you like to know more about any plan?"
    
    if intent == 'download':
        if is_premium:
            return "📥 **Download Options:**\n\n• Copy to Word (Free)\n• Download PDF (Premium ✓)\n• Download DOCX (Premium ✓)\n\nYour premium plan gives you full access! Just generate a lesson plan and click the download buttons."
        else:
            return "📥 **Download Options:**\n\n• Copy to Word (Free)\n• Download PDF (Premium)\n• Download DOCX (Premium)\n\n🔗 **Upgrade to Premium** to unlock all formats: /pricing/"
    
    if intent == 'create_account':
        return "📝 **Create a free account:**\n\n🔗 **Register here:** /register/\n\n**Benefits:**\n✅ 3 free lesson plans\n✅ Save your plans\n✅ Upgrade anytime\n\nIt takes less than a minute!"
    
    if intent == 'account_status':
        if is_authenticated:
            return f"📊 **Your Account Status:**\n\n👤 Username: {username}\n📧 Email: {email}\n💳 Plan: Free\n📝 Lessons used: {subscription_data.get('lessons_used', 0)}\n📝 Lessons remaining: {remaining}\n\n🔗 **Upgrade to Premium:** /pricing/ for unlimited access!"
        else:
            return "🔓 **You are not logged in.**\n\n🔗 Login: /login/\n🔗 Register: /register/\n\nCreate a free account to start generating lesson plans!"
    
    if intent == 'troubleshoot':
        return "🐛 **Troubleshooting Tips:**\n\n1. Clear your browser cache (Ctrl+Shift+Del)\n2. Refresh the page (Ctrl+F5)\n3. Try a different browser\n\n**Still having issues?**\n👉 **Chat with admin:** https://wa.me/250793599834"
    
    if intent == 'contact_admin':
        return "👨‍💼 **Contact Admin Directly:**\n\n📱 **WhatsApp:** 0793599834\n\n**Click to chat instantly:**\n👉 https://wa.me/250793599834\n\n📧 Email: support@isomoplus.com\n\nOur team will respond within 5-10 minutes!"
    
    if intent == 'payment_issue':
        return """💳 **Payment Issue Detected!**

Don't worry, we'll help you resolve this quickly.

**To help us activate your account faster, please have this information ready:**
📝 Your **Email address** (used to create your account)
📝 **Transaction ID** (check your MTN message)
📝 **Full name** used while paying

**👉 Click below to chat with admin on WhatsApp:**
https://wa.me/250793599834

📌 **Important:** Admin will respond within 5-10 minutes and activate your account after verification."""
    
    if intent == 'help':
        return "🤖 **I can help you with:**\n\n📝 Generating lesson plans\n💰 Subscription plans and pricing\n📥 Downloading your plans\n🔐 Account creation and login\n🐛 Troubleshooting issues\n💳 Payment issues\n\n**Still need help?** 👉 https://wa.me/250793599834\n\nWhat would you like to know?"
    
    if intent == 'thanks':
        return "🎉 **You're welcome!**\n\nI'm happy to help! Is there anything else you'd like to know about IsomoPlus?\n\n**Need more help?** 👉 https://wa.me/250793599834"
    
    if intent == 'goodbye':
        return "👋 **Goodbye!**\n\nCome back anytime if you need help with your lesson plans. Have a great day!\n\n📱 **Admin WhatsApp:** https://wa.me/250793599834"
    
    # Default response - includes WhatsApp link to admin
    return """🤔 **I'm not sure I understand. Let me help you better!**

**Here's what I can help with:**
• 📝 How to generate lesson plans
• 💰 Subscription plans and pricing
• 📥 Downloading your plan
• 🔐 Creating an account
• 🐛 Troubleshooting issues
• 💳 Payment problems

**Still need help?**
👉 **Chat with admin on WhatsApp:** https://wa.me/250793599834

Our team will respond within 5-10 minutes!

Please rephrase your question or click the link above to speak with someone directly."""


def get_suggestions(intent, is_premium):
    """Get follow-up suggestions based on intent"""
    
    suggestions_map = {
        'greeting': [
            "How do I generate a lesson plan?",
            "Tell me about subscription plans",
            "How do I download my plan?"
        ],
        'generate_lesson': [
            "How to select a subject?",
            "What if I can't find my unit?",
            "Can I edit the lesson title?"
        ],
        'pricing': [
            "Monthly plan details",
            "What payment methods are accepted?",
            "How to cancel subscription?"
        ],
        'download': [
            "PDF vs DOCX difference",
            "Why can't I download?",
            "How to copy to Word?"
        ],
        'create_account': [
            "Benefits of Premium account",
            "Forgot password help",
            "Account verification issues"
        ],
        'payment_issue': [
            "Contact admin directly",
            "Check payment status",
            "Request refund"
        ],
        'troubleshoot': [
            "Clear browser cache",
            "Update browser",
            "Contact support"
        ],
        'contact_admin': [
            "WhatsApp admin now",
            "Email support",
            "Call support"
        ]
    }
    
    # Premium users get different suggestions
    if is_premium:
        suggestions_map['premium'] = [
            "How to export to Google Docs?",
            "Bulk download multiple plans",
            "Share plans with colleagues"
        ]
    
    return suggestions_map.get(intent, [
        "How to generate a lesson plan?",
        "Check my subscription status",
        "Contact support"
    ])

def get_quick_actions(intent, is_authenticated):
    """Get quick action buttons to show"""
    
    if not is_authenticated:
        return [
            {'text': '📝 Create Account', 'action': 'redirect', 'url': '/register/'},
            {'text': '🔐 Login', 'action': 'redirect', 'url': '/login/'},
            {'text': '💰 View Pricing', 'action': 'redirect', 'url': '/pricing/'},
        ]
    
    actions_map = {
        'generate_lesson': [
            {'text': '📝 Generate Now', 'action': 'scroll_to_form', 'target': 'lessonForm'},
        ],
        'pricing': [
            {'text': '💰 Upgrade Now', 'action': 'redirect', 'url': '/pricing/'},
        ],
        'account_status': [
            {'text': '📊 Go to Dashboard', 'action': 'redirect', 'url': '/dashboard/'},
            {'text': '💰 Upgrade', 'action': 'redirect', 'url': '/pricing/'},
        ]
    }
    
    return actions_map.get(intent, [
        {'text': '📝 Generate Plan', 'action': 'scroll_to_form', 'target': 'lessonForm'},
        {'text': '💰 Pricing', 'action': 'redirect', 'url': '/pricing/'},
        {'text': '👨‍💼 Support', 'action': 'redirect', 'url': '/contact/'},
    ])


def save_conversation(user, conversation_id, user_message, bot_response, intent):
    """Save conversation to database for analytics"""
    try:
        # Import your model here (adjust as needed)
        # from lessons.models import ChatConversation
        # ChatConversation.objects.create(
        #     user=user,
        #     conversation_id=conversation_id,
        #     user_message=user_message,
        #     bot_response=bot_response,
        #     intent=intent,
        #     created_at=timezone.now()
        # )
        pass
    except Exception as e:
        logger.warning(f"Could not save conversation: {e}")


# Add to bot_views.py
def notify_admin_for_urgent_issues(intent, user_message, user):
    """Send email to admin for urgent issues"""
    urgent_intents = ['payment_issue', 'contact_admin', 'troubleshoot']
    
    if intent in urgent_intents:
        # Send email to admin
        from django.core.mail import send_mail
        send_mail(
            f'Urgent Bot Issue: {intent}',
            f'User: {user.email if user else "Anonymous"}\n'
            f'Message: {user_message}\n'
            f'Time: {timezone.now()}',
            'bot@isomoplus.com',
            ['admin@isomoplus.com'],
            fail_silently=True,
        )        

@csrf_exempt
@require_http_methods(["GET"])
def user_status_api(request):
    """Get current user's status for the chat bot - works for all users"""
    user = request.user if request.user.is_authenticated else None
    
    # For unauthenticated users
    if not user:
        return JsonResponse({
            'is_authenticated': False,
            'username': None,
            'email': None,
            'is_premium': False,
            'lessons_remaining': 3,
        })
    
    # For authenticated users
    data = {
        'is_authenticated': True,
        'username': user.username,
        'email': user.email,
        'is_premium': False,
        'lessons_remaining': 3,
    }
    
    # Check subscription if available
    if hasattr(user, 'subscription') and user.subscription:
        sub = user.subscription
        data['is_premium'] = getattr(sub, 'plan_name', 'free') in ['monthly', 'term', 'premium']
        data['plan'] = getattr(sub, 'plan_name', 'free')
        data['lessons_used'] = getattr(sub, 'lessons_generated', 0)
        data['lessons_remaining'] = 'unlimited' if data['is_premium'] else max(0, 3 - data['lessons_used'])
    
    return JsonResponse(data)


@csrf_exempt
@require_http_methods(["GET"])
def get_quick_replies(request):
    """API endpoint to get quick reply buttons"""
    from lessons.models import QuickReply  # Move import here
    replies = QuickReply.objects.filter(is_active=True).order_by('row', 'order')
    data = []
    for reply in replies:
        data.append({
            'text': reply.text,
            'message': reply.message,
            'icon': reply.icon,
            'row': reply.row,
        })
    return JsonResponse({'quick_replies': data})