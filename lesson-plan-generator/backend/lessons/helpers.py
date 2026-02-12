from django.shortcuts import get_object_or_404
from .models import Lesson, Unit, UserProfile, TeachingStrategy, LessonStrategyStep
from datetime import date

def prepare_lesson_plan_context(lesson_id, form_data, user=None, device_id=None):
    """
    Prepare all context needed for rendering a lesson plan table.
    - lesson_id: primary key of Lesson to fetch
    - form_data: dict/QueryDict from request.POST with additional inputs
    - user: Django user object (optional)
    - device_id: for guest users (optional)
    Returns: dict ready to pass to lesson_plan_table.html
    """
    # Get user profile (hybrid: guest or logged-in)
    if user:
        profile = get_object_or_404(UserProfile, user=user)
    else:
        profile, _ = UserProfile.objects.get_or_create(device_id=device_id)

    # Enforce free lesson limit
    if not profile.can_generate_plan():
        raise PermissionError(f"Free Lessons Limit Reached (Only {profile.get_current_lesson_limit()} Allowed)")

    # Fetch lesson object
    lesson = get_object_or_404(Lesson, pk=lesson_id)

    # Increment usage
    profile.use_lesson()

    # Prepare context for lesson plan table
    context = {
        'lesson_info': {
            'term': form_data.get('term', ''),
            'date': form_data.get('date', ''),
            'subject': lesson.unit.subject.name,
            'class_name': lesson.unit.subject.class_field.name,
            'lesson_title': lesson.title,
            'location_plan': form_data.get('location_plan', ''),
            'materials': form_data.get('materials', ''),
            'references': form_data.get('references', ''),
            'self_evaluation': form_data.get('self_evaluation', ''),
            'class_size': form_data.get('class_size', ''),
        },
        'unit_info': {
            'unit_number': lesson.unit.number,
            'unit_title': lesson.unit.title,
            'total_lessons': lesson.unit.total_lessons,
            'key_unit_competence': lesson.unit.key_unit_competence,
        },
        'lesson_number': lesson.number,
        'lesson_duration': form_data.get('duration', lesson.unit.total_lessons),
        'special_needs': form_data.get('special_needs', 'None'),
        'steps': lesson.strategy_steps.all().order_by('step_order'),
    }

    return context

# -----------------------------
# Helper: Build Lesson Plan Context
# -----------------------------
# File: /lesson-plan-generator/backend/lessons/helpers.py



def build_lesson_plan_context(request_data, profile):
    """
    Build full lesson plan context for rendering into lesson_plan_table.html.
    Handles:
    - Lesson and Unit info
    - Teaching strategy (with premium enforcement)
    - Steps (DB-driven or auto-generated fallback)
    - Defaults for lesson_number, lesson_duration, and special_needs
    Returns:
        dict: lesson_info, unit_info, steps, lesson_number, lesson_duration, special_needs
    """
    # -----------------------------
    # Fetch Unit and Lesson
    # -----------------------------
    unit_id = request_data.get("unit_id")
    lesson_id = request_data.get("lesson_id")

    unit = get_object_or_404(Unit, id=unit_id) if unit_id else None
    lesson = get_object_or_404(Lesson, id=lesson_id) if lesson_id else None

    # -----------------------------
    # Resolve Strategy
    # -----------------------------
    strategy_input = request_data.get("strategy")
    selected_strategy = None

    if strategy_input:
        if str(strategy_input).isdigit():
            selected_strategy = TeachingStrategy.objects.filter(
                id=strategy_input, is_active=True
            ).first()
        else:
            selected_strategy = TeachingStrategy.objects.filter(
                name__iexact=strategy_input, is_active=True
            ).first()

    # Fallback to first active strategy
    if not selected_strategy:
        selected_strategy = TeachingStrategy.objects.filter(is_active=True).order_by("id").first()

    if not selected_strategy:
        raise ValueError("No active teaching strategies found")

    # Premium enforcement
    if selected_strategy.is_premium_only and not profile.is_subscription_active():
        raise PermissionError("This strategy is premium only")

    # -----------------------------
    # Build Lesson Info with Safe Defaults
    # -----------------------------
    lesson_info = {
        "school_name": request_data.get("school_name") or profile.school_name or "N/A",
        "teacher_name": request_data.get("teacher_name") or profile.teacher_name or "N/A",
        "term": request_data.get("term") or profile.default_term or "N/A",
        "class_size": request_data.get("class_size") or profile.class_size or 0,
        "references": request_data.get("references") or (lesson.references if lesson else profile.references) or "No references provided",
        "lesson_title": lesson.title if lesson else "Untitled Lesson",
        "class_name": request_data.get("class") or "N/A",
        "level": request_data.get("level") or "N/A",
        "subject": request_data.get("subject") or (unit.subject.name if unit and unit.subject else "N/A"),
        "date": request_data.get("date") or str(date.today()),
        "strategy": selected_strategy.name,
        "location_plan": request_data.get("location_plan") or "Not specified",
        "materials": request_data.get("materials") or "Not specified",
        "self_evaluation": request_data.get("self_evaluation") or "Not completed by teacher."
    }

    # -----------------------------
    # Build Unit Info
    # -----------------------------
    unit_info = {
        "unit_number": getattr(unit, "number", 1) if unit else 1,
        "unit_title": unit.title if unit else lesson_info["lesson_title"],
        "key_unit_competence": getattr(unit, "key_unit_competence", f"Understand {lesson_info['lesson_title']}"),
        "total_lessons": unit.lessons.count() if unit and hasattr(unit, "lessons") else 1
    }

    # -----------------------------
    # Build Steps (Database Driven with Fallback)
    # -----------------------------
    steps = []

    if lesson and selected_strategy:
        strategy_steps = LessonStrategyStep.objects.filter(
            lesson=lesson,
            strategy=selected_strategy
        ).order_by("step_order")

        if strategy_steps.exists():
            for step in strategy_steps:
                steps.append({
                    "title": f"{step.step_order}: {step.step_title}",
                    "duration_minutes": step.duration_minutes,
                    "teacher_activity": step.teacher_activity,
                    "learner_activity": step.learner_activity,
                    "competence": step.generic_competence
                })
        else:
            steps = [
                {
                    "title": "1: Introduction",
                    "duration_minutes": 10,
                    "teacher_activity": "Introduce the lesson objectives and activate prior knowledge.",
                    "learner_activity": "Listen, respond to questions, and share prior ideas.",
                    "competence": "Communication"
                },
                {
                    "title": "2: Development",
                    "duration_minutes": 20,
                    "teacher_activity": f"Explain and guide activities on {lesson_info['lesson_title']}.",
                    "learner_activity": "Participate in guided activities and discussions.",
                    "competence": "Critical Thinking"
                },
                {
                    "title": "3: Conclusion",
                    "duration_minutes": 10,
                    "teacher_activity": "Summarize key points and assess understanding.",
                    "learner_activity": "Ask questions and reflect on learning.",
                    "competence": "Collaboration"
                }
            ]

    # -----------------------------
    # Lesson Meta Values
    # -----------------------------
    lesson_number = request_data.get("lesson_no", lesson.number if lesson else 1)
    lesson_duration = request_data.get("duration", 40)
    special_needs = request_data.get("special_needs") or "No specific special educational needs identified in this class"

    # -----------------------------
    # Final Context
    # -----------------------------
    return {
        "lesson_info": lesson_info,
        "unit_info": unit_info,
        "steps": steps,
        "lesson_number": lesson_number,
        "lesson_duration": lesson_duration,
        "special_needs": special_needs
    }
