"""
lessons/helpers.py
==================
Single-page lesson plan context builder (CBC-Complete Edition).

One call → one lesson × one strategy × exactly 3 steps = one printable page.

Exported functions:
  prepare_lesson_plan_context()   – legacy helper (unchanged)
  build_lesson_plan_context()     – SINGLE-PAGE builder (updated)
"""

import random
from django.shortcuts import get_object_or_404
from .models import Lesson, Unit, UserProfile, TeachingStrategy, LessonStrategyStep
from datetime import date


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC INSTRUCTIONAL OBJECTIVE TEMPLATES (5 professional CBC formats)
# ─────────────────────────────────────────────────────────────────────────────
#
# Each template uses {title} as the only placeholder.
# They rotate randomly so every plan feels freshly written.
#
# Format styles:
#   1 — Concrete/semi-concrete materials (hands-on, STEM-friendly)
#   2 — Bloom's taxonomy (action verb + condition + measurable criterion)
#   3 — Full ABCD (Audience · Behaviour · Condition · Degree) — audit-ready
#   4 — Collaborative / inquiry-based (21st-century skills focus)
#   5 — Differentiated / inclusive (SEN-aware, strong CBC compliance)

OBJECTIVE_TEMPLATES = [
    # 1 — Concrete / semi-concrete
    (
        "By using concrete and semi-concrete materials, learners will be able to "
        "demonstrate understanding of {title}, achieving a minimum accuracy of 80% "
        "in both practical and written tasks."
    ),
    # 2 — Bloom's taxonomy
    (
        "Given guided practice and peer discussion, learners will accurately "
        "explain, apply, and evaluate key concepts of {title}, "
        "scoring at least 4 out of 5 on formative assessment tasks."
    ),
    # 3 — Full ABCD format
    (
        "Learners (A) will be able to analyse and solve problems related to {title} (B), "
        "using classroom resources and teacher-guided worked examples (C), "
        "with a minimum success rate of 80% on assessed tasks (D)."
    ),
    # 4 — Collaborative / inquiry-based
    (
        "Through collaborative inquiry and teacher-facilitated activities, "
        "learners will construct, communicate, and justify their understanding of {title}, "
        "demonstrating mastery in both written responses and oral presentations."
    ),
    # 5 — Differentiated / inclusive
    (
        "By the end of this lesson, all learners — including those with special "
        "educational needs — will be able to identify, describe, and apply "
        "the core concepts of {title} using appropriately differentiated "
        "support materials and strategies."
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# TEACHER SELF-EVALUATION OPTIONS
# Rendered as tick-box choices in the template.
# ─────────────────────────────────────────────────────────────────────────────

SELF_EVALUATION_OPTIONS = [
    "Lesson objective fully achieved — learners demonstrated mastery.",
    "Lesson objective partially achieved — some learners need follow-up support.",
    "Lesson needs to be repeated — majority of learners did not meet the objective.",
    "Lesson pace adjusted — content will continue in the next lesson.",
]


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY HELPER (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def prepare_lesson_plan_context(lesson_id, form_data, user=None, device_id=None):
    """
    Prepare all context needed for rendering a lesson plan table.
    Handles default location/materials and multi-select materials.
    """

    if user:
        profile = get_object_or_404(UserProfile, user=user)
    else:
        profile, _ = UserProfile.objects.get_or_create(device_id=device_id)

    if not profile.can_generate_plan():
        raise PermissionError(
            f"Free Lessons Limit Reached (Only {profile.get_current_lesson_limit()} Allowed)"
        )

    lesson = get_object_or_404(Lesson, pk=lesson_id)
    unit = lesson.unit
    subject_name = unit.subject.name if unit.subject else "N/A"

    if subject_name == "Computer Science":
        default_materials = ["Computer", "Projector", "IDE software"]
        default_location = "Computer laboratory"
    elif subject_name == "Biology":
        default_materials = ["Charts", "Microscope", "Specimens"]
        default_location = "Laboratory"
    elif subject_name == "Chemistry":
        default_materials = ["Laboratory apparatus", "Chemicals", "Safety equipment"]
        default_location = "Laboratory"
    elif subject_name == "Physics":
        default_materials = ["Laboratory equipment", "Measuring instruments"]
        default_location = "Laboratory"
    else:
        default_materials = ["Textbook", "Chalkboard"]
        default_location = "Inside classroom"

    location_plan = form_data.get("location_plan") or default_location

    if hasattr(form_data, "getlist"):
        materials_list = form_data.getlist("materials")
    else:
        materials_list = form_data.get("materials")
        if isinstance(materials_list, str):
            materials_list = [m.strip() for m in materials_list.split(",") if m.strip()]
        elif not isinstance(materials_list, list):
            materials_list = []

    materials = ", ".join(materials_list) if materials_list else ", ".join(default_materials)

    context = {
        'lesson_info': {
            'term': form_data.get('term', ''),
            'date': form_data.get('date', ''),
            'subject': subject_name,
            'class_name': unit.subject.class_field.name if unit.subject and hasattr(unit.subject, "class_field") else "",
            'location_plan': location_plan,
            'materials': materials,
            'references': form_data.get('references', ''),
            'self_evaluation': form_data.get('self_evaluation', ''),
            'class_size': form_data.get('class_size', ''),
        },
        'unit_info': {
            'unit_number': unit.number,
            'unit_title': unit.title,
            'total_lessons': getattr(unit, "total_lessons", 1),
            'key_unit_competence': getattr(unit, "key_unit_competence", f"Understand {lesson.title}"),
        },
        'lesson_number': lesson.number,
        'lesson_duration': form_data.get('duration', 40),
        'special_needs': form_data.get('special_needs', 'None'),
        'steps': lesson.strategy_steps.all().order_by('step_order'),
    }

    return context


# ─────────────────────────────────────────────────────────────────────────────
# SINGLE-PAGE LESSON PLAN CONTEXT BUILDER (CBC-Complete)
# ─────────────────────────────────────────────────────────────────────────────

def build_lesson_plan_context(request_data, profile):
    """
    Build a SINGLE-PAGE lesson plan context for one lesson × one strategy.

    One page = one lesson, one strategy, exactly 3 steps:
        1: Introduction  (≈20 % of duration)
        2: Development   (≈60 % of duration)
        3: Conclusion    (≈20 % of duration)

    CBC-complete fields (lesson_description, instructional_objective,
    cross_cutting_issues) are always populated — from the DB when seeded,
    or from deterministic fallbacks otherwise.

    Args:
        request_data  – dict-like (QueryDict or plain dict) from the request
        profile       – UserProfile instance for the current user/guest

    Returns a flat dict:
        lesson_info              – school/teacher/class/subject/date/term/refs/etc.
        unit_info                – unit number, title, key_unit_competence, total_lessons
        lesson_number            – int
        lesson_duration          – int (total minutes for the lesson)
        special_needs            – str
        lesson_description       – str  (1-2 sentences, from seeded step 1)
        instructional_objective  – str  (dynamic CBC format, randomly selected)
        #cross_cutting_issues     – str  (CBC-required, from seeded step 1)
        steps                    – list of exactly 3 step dicts
        self_evaluation_options  – list of 4 tick-box strings for teacher evaluation
        is_single_page           – True  (template flag)
    """

    # ── 1. Resolve Lesson & Unit ──────────────────────────────────────────────
    lesson_id = request_data.get("lesson_id")

    if not lesson_id:
        raise ValueError("lesson_id is required to build a single-page lesson plan.")

    lesson = get_object_or_404(Lesson, id=lesson_id)
    unit   = lesson.unit          # always follow the FK — never a separate unit_id lookup

    # ── 2. Resolve Teaching Strategy ─────────────────────────────────────────
    strategy_input    = request_data.get("strategy")
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

    # Fallback → first free active strategy (safe for guest/free users)
    if not selected_strategy:
        selected_strategy = (
            TeachingStrategy.objects
            .filter(is_active=True, is_premium_only=False)
            .order_by("id")
            .first()
        )

    if not selected_strategy:
        raise ValueError("No active teaching strategy found in the database.")

    # Premium gate
    if selected_strategy.is_premium_only and not profile.is_subscription_active():
        raise PermissionError(
            "The selected strategy is available to premium subscribers only."
        )

    # ── 3. lesson_info ────────────────────────────────────────────────────────
    subject_name = unit.subject.name if unit and unit.subject else "N/A"
    class_name   = (
        unit.subject.class_field.name
        if unit and unit.subject and hasattr(unit.subject, "class_field")
        else request_data.get("class", "N/A")
    )

    lesson_info = {
        "school_name":     request_data.get("school_name")    or profile.school_name   or "N/A",
        "teacher_name":    request_data.get("teacher_name")   or profile.teacher_name  or "N/A",
        "term":            request_data.get("term")            or profile.default_term  or "N/A",
        "class_size":      request_data.get("class_size")      or profile.class_size    or 0,
        "references":      (
            request_data.get("references")
            or lesson.references
            or (profile.references or "No references provided")
        ),
        "lesson_title":    lesson.title,
        "class_name":      class_name,
        "level":           request_data.get("level", "N/A"),
        "subject":         subject_name,
        "date":            request_data.get("date") or str(date.today()),
        "strategy":        selected_strategy.name,
        "location_plan":   request_data.get("location_plan") or "Inside classroom",
        "materials":       request_data.get("materials")     or "Textbook, Chalkboard",
        # self_evaluation is now handled via self_evaluation_options tick-boxes
        # kept here for legacy / any custom text the teacher adds after
        "self_evaluation": request_data.get("self_evaluation") or "",
    }

    # ── 4. unit_info ──────────────────────────────────────────────────────────
    unit_info = {
        "unit_number":         unit.number,
        "unit_title":          unit.title,
        "key_unit_competence": getattr(unit, "key_unit_competence", f"Understand {lesson.title}"),
        "total_lessons":       unit.lessons.count() if hasattr(unit, "lessons") else 1,
    }

    # ── 5. Steps — exactly 3 for one page ────────────────────────────────────
    steps                   = []
    lesson_description      = None
    instructional_objective = None

    db_steps = (
        LessonStrategyStep.objects
        .filter(lesson=lesson, strategy=selected_strategy)
        .order_by("step_order")[:3]   # hard-cap at 3 — one page only
    )

    if db_steps.exists():
        # ── DB path: use seeded content ───────────────────────────────────────
        for step in db_steps:
            if step.step_order == 1:
                # Pull CBC-complete fields from step 1
                lesson_description = (
                    step.lesson_description
                    or f"This lesson explores {lesson.title} through structured learning activities."
                )
                # Use seeded objective if available, otherwise pick a dynamic template
                instructional_objective = (
                    step.instructional_objective
                    or random.choice(OBJECTIVE_TEMPLATES).format(title=lesson.title)
                )
                
            steps.append({
                "title":                  f"{step.step_order}: {step.step_title}",
                "duration_minutes":       step.duration_minutes,
                "teacher_activity":       step.teacher_activity,
                "learner_activity":       step.learner_activity,
                "competence":             step.generic_competence or "Communication",
                "competence_integration": (
                    step.competence_integration
                    or f"{step.generic_competence} is developed through active engagement in this step."
                ),
            })

    else:
        # ── Fallback path: no seeded steps yet ───────────────────────────────
        title   = lesson.title
        dur     = int(request_data.get("duration", 40))
        intro_d = round(dur * 0.20)
        dev_d   = round(dur * 0.60)
        conc_d  = dur - intro_d - dev_d

        lesson_description = (
            f"This lesson explores {title} through guided practice and collaborative learning."
        )

        # ── Dynamic instructional objective — randomly pick one of 5 formats ──
        instructional_objective = random.choice(OBJECTIVE_TEMPLATES).format(title=title)
        steps = [
            {
                "title":                  "1: Introduction",
                "duration_minutes":       intro_d,
                "teacher_activity":       (
                    f"Introduce the lesson objectives for {title} and "
                    "activate prior knowledge through structured questioning."
                ),
                "learner_activity":       (
                    "Listen attentively, respond to questions, and share prior knowledge."
                ),
                "competence":             "Communication and Critical Thinking",
                "competence_integration": (
                    "Communication is developed as learners articulate prior knowledge "
                    "through teacher-led questioning. "
                    "Critical thinking is activated as learners connect new topics "
                    "to existing knowledge."
                ),
            },
            {
                "title":                  "2: Development",
                "duration_minutes":       dev_d,
                "teacher_activity":       (
                    f"Guide learners through key concepts and activities on {title}. "
                    "Facilitate peer discussion and provide formative feedback."
                ),
                "learner_activity":       (
                    "Participate in guided activities, discuss with peers, "
                    "and apply concepts to practice tasks."
                ),
                "competence":             "Critical Thinking, Problem-Solving, and Collaboration",
                "competence_integration": (
                    "Critical thinking deepens as learners analyse and break down concepts. "
                    "Problem-solving is practised through structured application exercises. "
                    "Collaboration is fostered as learners work in pairs or groups "
                    "to complete tasks and share findings."
                ),
            },
            {
                "title":                  "3: Conclusion",
                "duration_minutes":       conc_d,
                "teacher_activity":       (
                    f"Summarise key points about {title}, reinforce the unit competence, "
                    "and assign a brief reflection or homework task."
                ),
                "learner_activity":       (
                    "Reflect on learning, ask remaining questions, "
                    "and record homework in exercise books."
                ),
                "competence":             "Self-Regulation and Communication",
                "competence_integration": (
                    "Self-regulation is practised as learners reflect on what they have "
                    "understood and identify areas needing further review. "
                    "Communication is reinforced as learners articulate key takeaways "
                    "from the lesson in their own words."
                ),
            },
        ]

    # ── 6. Page-level meta ────────────────────────────────────────────────────
    lesson_number   = request_data.get("lesson_no", lesson.number)
    lesson_duration = int(request_data.get("duration", 40))
    special_needs   = (
        request_data.get("special_needs")
        or "No specific special educational needs identified in this class."
    )

    # ── 7. Return single-page context ─────────────────────────────────────────
    return {
        # Identity / header rows
        "lesson_info":             lesson_info,
        "unit_info":               unit_info,
        # Page-level scalars
        "lesson_number":           lesson_number,
        "lesson_duration":         lesson_duration,
        "special_needs":           special_needs,
        # CBC-complete lesson-level fields (always populated)
        "lesson_description":      lesson_description,
        "instructional_objective": instructional_objective,
        # Exactly 3 step rows → renders as one page
        "steps":                   steps,
        # 4 tick-box options for teacher self-evaluation
        "self_evaluation_options": SELF_EVALUATION_OPTIONS,
        # Convenience flag for template conditionals
        "is_single_page":          True,
    }