"""
Management Command: seed_strategies_per_lesson
================================================
CBC Lesson Plan Generator – Professional Strategy Seeder
--------------------------------------------------------
Seeds 3 strategies per lesson driven by key_unit_competence and lesson title.

Strategies:
  1. Discussion Method         (FREE)
  2. Group Collaborative Work  (FREE)
  3. Project-Based Learning    (PREMIUM)

Each lesson gets 3 steps per strategy:
  - Introduction  (20% duration)
  - Development   (60% duration)
  - Conclusion    (20% duration)

Step content is generated from:
  - lesson.title
  - unit.key_unit_competence
  - unit.title
  - strategy pedagogical pattern

Usage:
  python manage.py seed_strategies_per_lesson
  python manage.py seed_strategies_per_lesson --clear   # wipe and reseed
  python manage.py seed_strategies_per_lesson --lesson_id 5  # single lesson
"""

from django.core.management.base import BaseCommand
from lessons.models import (
    Lesson,
    TeachingStrategy,
    LessonStrategyStep,
)


# ─────────────────────────────────────────────────────────────────────────────
# STRATEGY DEFINITIONS
# 3 strategies: 2 free, 1 premium
# ─────────────────────────────────────────────────────────────────────────────

STRATEGIES = [
    {
        "name": "Discussion Method",
        "description": (
            "Teacher facilitates structured classroom discussion, activating "
            "prior knowledge and guiding learners to construct understanding "
            "through questioning and peer interaction."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Group Collaborative Work",
        "description": (
            "Learners work in small groups to investigate, solve problems, "
            "and present findings. Teacher circulates as a facilitator, "
            "promoting teamwork and communication competences."
        ),
        "is_premium_only": False,
        "is_active": True,
    },
    {
        "name": "Project-Based Learning",
        "description": (
            "Premium strategy. Learners design and build real-world solutions "
            "tied to the unit competence. Teacher coaches and evaluates through "
            "observation and structured feedback sessions."
        ),
        "is_premium_only": True,
        "is_active": True,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# STEP TEMPLATE ENGINE
# Generates 3 steps per (lesson, strategy) using competence + lesson title
# Duration split: 20% / 60% / 20%
# ─────────────────────────────────────────────────────────────────────────────

def generate_steps(lesson, strategy, total_duration=40):
    """
    Returns a list of 3 step dicts for (lesson × strategy).
    Content is driven by lesson.title and unit.key_unit_competence.
    Duration is split proportionally: 20/60/20.
    """

    title = lesson.title
    unit = lesson.unit
    competence = getattr(unit, "key_unit_competence", f"understand {title}")
    unit_title = getattr(unit, "title", title)
    strategy_name = strategy.name

    # Duration calculation (20 / 60 / 20 percent)
    intro_dur = round(total_duration * 0.20)
    dev_dur = round(total_duration * 0.60)
    conc_dur = total_duration - intro_dur - dev_dur  # absorb rounding remainder

    # ── DISCUSSION METHOD ─────────────────────────────────────────────────────
    if strategy_name == "Discussion Method":
        return [
            {
                "order": 1,
                "title": "Introduction",
                "duration": intro_dur,
                "teacher": (
                    f"Welcome learners and introduce the topic: {title}. "
                    f"Pose open-ended questions to activate prior knowledge about {unit_title}. "
                    f"State the lesson objective aligned to: {competence}."
                ),
                "learner": (
                    f"Listen attentively and respond to the teacher's questions. "
                    f"Share what they already know about {title} and connect ideas "
                    f"from previous lessons."
                ),
                "competence": "Communication and Critical Thinking",
            },
            {
                "order": 2,
                "title": "Development",
                "duration": dev_dur,
                "teacher": (
                    f"Facilitate a structured whole-class and pair discussion on key concepts "
                    f"of {title}. Use probing questions to deepen understanding of {competence}. "
                    f"Write key points on the board and guide learners to draw conclusions."
                ),
                "learner": (
                    f"Participate actively in the discussion by sharing ideas, asking questions, "
                    f"and building on peers' contributions. Take notes on key concepts of {title} "
                    f"and relate them to real-life applications."
                ),
                "competence": "Critical Thinking, Communication, and Lifelong Learning",
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration": conc_dur,
                "teacher": (
                    f"Summarise the key points from the discussion on {title}. "
                    f"Reinforce the unit competence: {competence}. "
                    f"Assign a short reflection task or homework."
                ),
                "learner": (
                    f"Reflect on what was learned about {title}. "
                    f"Ask any remaining questions and note the teacher's summary. "
                    f"Record homework or follow-up tasks in their exercise books."
                ),
                "competence": "Self-Regulation and Communication",
            },
        ]

    # ── GROUP COLLABORATIVE WORK ──────────────────────────────────────────────
    elif strategy_name == "Group Collaborative Work":
        return [
            {
                "order": 1,
                "title": "Introduction",
                "duration": intro_dur,
                "teacher": (
                    f"Set the context for {title} by briefly explaining the activity objectives. "
                    f"Divide learners into groups of 4–5 and distribute task sheets "
                    f"aligned to {competence}. "
                    f"Clarify roles: facilitator, recorder, presenter, timekeeper."
                ),
                "learner": (
                    f"Move into assigned groups and read the task instructions. "
                    f"Clarify any questions about the activity on {title}. "
                    f"Agree on roles within the group."
                ),
                "competence": "Cooperation and Communication",
            },
            {
                "order": 2,
                "title": "Development",
                "duration": dev_dur,
                "teacher": (
                    f"Move between groups to monitor progress and provide targeted guidance "
                    f"on {title}. Ask probing questions to deepen group discussions. "
                    f"Ensure all groups stay focused on achieving {competence}. "
                    f"Note observations for feedback during conclusion."
                ),
                "learner": (
                    f"Collaborate to investigate, solve tasks, and discuss concepts related "
                    f"to {title}. The recorder documents findings while the facilitator "
                    f"keeps the group on task. Prepare a short group presentation of key "
                    f"findings to share with the class."
                ),
                "competence": "Teamwork, Problem-Solving, and Critical Thinking",
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration": conc_dur,
                "teacher": (
                    f"Invite 1–2 groups to present their findings on {title}. "
                    f"Offer constructive feedback and correct any misconceptions. "
                    f"Consolidate learning by restating the key competence: {competence}."
                ),
                "learner": (
                    f"Group presenters share key findings on {title}. "
                    f"Other learners listen, take notes, and ask follow-up questions. "
                    f"Reflect individually on what the group activity added to their "
                    f"understanding."
                ),
                "competence": "Communication, Lifelong Learning, and Self-Regulation",
            },
        ]

    # ── PROJECT-BASED LEARNING (PREMIUM) ─────────────────────────────────────
    elif strategy_name == "Project-Based Learning":
        return [
            {
                "order": 1,
                "title": "Introduction",
                "duration": intro_dur,
                "teacher": (
                    f"Introduce the project brief for {title}. "
                    f"Explain the driving question aligned to {competence} and the "
                    f"real-world context of {unit_title}. "
                    f"Outline deliverables, milestones, and success criteria. "
                    f"Assign project teams and distribute resource materials."
                ),
                "learner": (
                    f"Review the project brief for {title} and ask clarifying questions. "
                    f"Understand the expected deliverable and how it connects to {competence}. "
                    f"Form teams, assign roles, and begin initial project planning."
                ),
                "competence": "Critical Thinking, Communication, and Creativity",
            },
            {
                "order": 2,
                "title": "Development",
                "duration": dev_dur,
                "teacher": (
                    f"Coach individual teams as they design and build their solution for {title}. "
                    f"Provide formative feedback on progress and redirect teams that deviate "
                    f"from the competence goal: {competence}. "
                    f"Model problem-solving techniques and prompt deeper inquiry."
                ),
                "learner": (
                    f"Research, design, and develop their project solution related to {title}. "
                    f"Collaborate within teams, make decisions, test ideas, and refine the "
                    f"solution to meet the requirements of {competence}. "
                    f"Document progress in a project logbook."
                ),
                "competence": "Problem-Solving, Research, Creativity, and Collaboration",
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration": conc_dur,
                "teacher": (
                    f"Facilitate project presentations or demonstrations on {title}. "
                    f"Evaluate each team using a rubric aligned to {competence}. "
                    f"Provide structured feedback and highlight best practices observed. "
                    f"Connect the project outcomes back to the unit competence."
                ),
                "learner": (
                    f"Present or demonstrate their completed project on {title} to the class. "
                    f"Respond to questions from the teacher and peers. "
                    f"Reflect on the project experience and write a brief self-assessment "
                    f"on how well they achieved {competence}."
                ),
                "competence": "Communication, Self-Regulation, and Critical Thinking",
            },
        ]

    # ── FALLBACK (generic, should never trigger if strategies are seeded correctly)
    else:
        return [
            {
                "order": 1,
                "title": "Introduction",
                "duration": intro_dur,
                "teacher": f"Introduce {title} and state lesson objectives.",
                "learner": f"Listen and respond to introductory questions about {title}.",
                "competence": "Communication",
            },
            {
                "order": 2,
                "title": "Development",
                "duration": dev_dur,
                "teacher": f"Guide learners through key activities on {title}.",
                "learner": f"Participate in guided activities and discussions on {title}.",
                "competence": "Critical Thinking",
            },
            {
                "order": 3,
                "title": "Conclusion",
                "duration": conc_dur,
                "teacher": f"Summarise key points and reinforce: {competence}.",
                "learner": f"Ask questions and reflect on learning about {title}.",
                "competence": "Self-Regulation",
            },
        ]


# ─────────────────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = (
        "Seed professional teaching strategies and lesson steps for every lesson "
        "in the database. Steps are driven by each lesson's key_unit_competence."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            default=False,
            help="Delete all existing LessonStrategyStep records before reseeding.",
        )
        parser.add_argument(
            "--lesson_id",
            type=int,
            default=None,
            help="Seed steps for a single lesson ID only.",
        )
        parser.add_argument(
            "--duration",
            type=int,
            default=40,
            help="Default lesson duration in minutes (default: 40).",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "\n🔥 CBC Strategy Seeder — Per-Lesson Intelligence Mode\n"
            "─────────────────────────────────────────────────────"
        ))

        # ── Optional: clear all existing steps
        if options["clear"]:
            deleted, _ = LessonStrategyStep.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f"  ⚠️  Cleared {deleted} existing LessonStrategyStep records."
            ))

        # ── Upsert strategies
        strategy_objects = {}
        for s_def in STRATEGIES:
            strategy, created = TeachingStrategy.objects.update_or_create(
                name=s_def["name"],
                defaults={
                    "description": s_def["description"],
                    "is_premium_only": s_def["is_premium_only"],
                    "is_active": s_def["is_active"],
                },
            )
            strategy_objects[s_def["name"]] = strategy
            status = "✅ Created" if created else "🔄 Updated"
            tier = "PREMIUM" if s_def["is_premium_only"] else "FREE"
            self.stdout.write(f"  {status} strategy [{tier}]: {strategy.name}")

        self.stdout.write("")

        # ── Fetch lessons
        lessons_qs = Lesson.objects.select_related("unit__subject__class_field")
        if options["lesson_id"]:
            lessons_qs = lessons_qs.filter(id=options["lesson_id"])
            if not lessons_qs.exists():
                self.stdout.write(self.style.ERROR(
                    f"  ❌ No lesson found with id={options['lesson_id']}"
                ))
                return

        total_lessons = lessons_qs.count()
        if total_lessons == 0:
            self.stdout.write(self.style.ERROR(
                "  ❌ No lessons found in database. "
                "Run bulk_upload_units or seed_full_computer first."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"  📚 Seeding steps for {total_lessons} lesson(s) × "
            f"{len(STRATEGIES)} strategies × 3 steps each...\n"
        ))

        duration = options["duration"]
        created_count = 0
        skipped_count = 0
        lesson_count = 0

        # ── Main loop: lesson × strategy
        for lesson in lessons_qs.order_by("unit__number", "number"):
            lesson_count += 1
            lesson_label = (
                f"Unit {lesson.unit.number} | Lesson {lesson.number}: {lesson.title}"
            )
            self.stdout.write(f"  📖 [{lesson_count}/{total_lessons}] {lesson_label}")

            for strategy in strategy_objects.values():
                steps = generate_steps(lesson, strategy, total_duration=duration)

                for step in steps:
                    _, step_created = LessonStrategyStep.objects.update_or_create(
                        lesson=lesson,
                        strategy=strategy,
                        step_order=step["order"],
                        defaults={
                            "step_title": step["title"],
                            "duration_minutes": step["duration"],
                            "teacher_activity": step["teacher"],
                            "learner_activity": step["learner"],
                            "generic_competence": step["competence"],
                        },
                    )
                    if step_created:
                        created_count += 1
                    else:
                        skipped_count += 1

            self.stdout.write(
                f"       └─ 3 strategies × 3 steps seeded ✓"
            )

        # ── Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n{'─' * 53}\n"
            f"  ✅ Seeding complete.\n"
            f"     Lessons processed : {lesson_count}\n"
            f"     Steps created     : {created_count}\n"
            f"     Steps updated     : {skipped_count}\n"
            f"     Total steps in DB : {created_count + skipped_count}\n"
            f"{'─' * 53}\n"
        ))
