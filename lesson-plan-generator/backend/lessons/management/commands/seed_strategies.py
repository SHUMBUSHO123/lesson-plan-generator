from django.core.management.base import BaseCommand
from lessons.models import (
    TeachingStrategy,
    LessonStrategyStep,
    Lesson,
    Unit
)


class Command(BaseCommand):
    help = "Seed sample strategies and lesson strategy steps for Senior Six Computer"

    def handle(self, *args, **kwargs):

        # --------------------------------------------------
        # 1️⃣ Ensure At Least One Lesson Exists
        # --------------------------------------------------
        lesson = Lesson.objects.first()

        if not lesson:
            self.stdout.write(self.style.ERROR("No Lesson found in database."))
            return

        self.stdout.write(self.style.SUCCESS(f"Using Lesson: {lesson.title}"))

        # --------------------------------------------------
        # 2️⃣ Create Strategies
        # --------------------------------------------------
        discussion_strategy, _ = TeachingStrategy.objects.get_or_create(
            name="Discussion Method",
            defaults={
                "description": "Interactive class discussion approach.",
                "is_active": True,
                "is_premium_only": False
            }
        )

        project_strategy, _ = TeachingStrategy.objects.get_or_create(
            name="Project-Based Learning",
            defaults={
                "description": "Students build real-world computer projects.",
                "is_active": True,
                "is_premium_only": True
            }
        )

        self.stdout.write(self.style.SUCCESS("Strategies created/verified."))

        # --------------------------------------------------
        # 3️⃣ Clear Old Steps For Clean Seeding
        # --------------------------------------------------
        LessonStrategyStep.objects.filter(
            lesson=lesson,
            strategy__in=[discussion_strategy, project_strategy]
        ).delete()

        # --------------------------------------------------
        # 4️⃣ Seed Discussion Strategy Steps (FREE)
        # --------------------------------------------------
        LessonStrategyStep.objects.create(
            lesson=lesson,
            strategy=discussion_strategy,
            step_order=1,
            step_title="Introduction to Concepts",
            duration_minutes=10,
            teacher_activity="Introduce topic and pose discussion questions.",
            learner_activity="Respond to questions and share prior knowledge."
        )

        LessonStrategyStep.objects.create(
            lesson=lesson,
            strategy=discussion_strategy,
            step_order=2,
            step_title="Guided Discussion",
            duration_minutes=25,
            teacher_activity="Facilitate group discussion on computer concepts.",
            learner_activity="Participate in structured discussion."
        )

        LessonStrategyStep.objects.create(
            lesson=lesson,
            strategy=discussion_strategy,
            step_order=3,
            step_title="Summary & Reflection",
            duration_minutes=5,
            teacher_activity="Summarize key learning points.",
            learner_activity="Reflect and ask clarifying questions."
        )

        # --------------------------------------------------
        # 5️⃣ Seed Project-Based Strategy Steps (PREMIUM)
        # --------------------------------------------------
        LessonStrategyStep.objects.create(
            lesson=lesson,
            strategy=project_strategy,
            step_order=1,
            step_title="Project Briefing",
            duration_minutes=10,
            teacher_activity="Explain project requirements and objectives.",
            learner_activity="Understand project scope and deliverables."
        )

        LessonStrategyStep.objects.create(
            lesson=lesson,
            strategy=project_strategy,
            step_order=2,
            step_title="Hands-On Development",
            duration_minutes=25,
            teacher_activity="Guide students while building mini software solution.",
            learner_activity="Develop practical computer-based solution."
        )

        LessonStrategyStep.objects.create(
            lesson=lesson,
            strategy=project_strategy,
            step_order=3,
            step_title="Presentation & Feedback",
            duration_minutes=5,
            teacher_activity="Evaluate and give feedback.",
            learner_activity="Present project and receive feedback."
        )

        self.stdout.write(self.style.SUCCESS("Lesson strategy steps seeded successfully."))
