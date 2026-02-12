from django.core.management.base import BaseCommand
from lessons.models import Level, Class, Subject, Unit, Lesson, TeachingStrategy, LessonStrategyStep

class Command(BaseCommand):
    help = 'Seed full Senior Six Computer Science curriculum with strategies and steps'

    def handle(self, *args, **options):
        print('🔥 Seeding full Computer Science curriculum...')

        # -----------------------------
        # 1. Level
        # -----------------------------
        level, _ = Level.objects.get_or_create(name='Senior Six')
        print(f'Level created/verified: {level}')

        # -----------------------------
        # 2. Class
        # -----------------------------
        cls, _ = Class.objects.get_or_create(level=level, name='Computer Science')
        print(f'Class created/verified: {cls}')

        # -----------------------------
        # 3. Subject
        # -----------------------------
        subject, _ = Subject.objects.get_or_create(class_field=cls, name='Computer Science')
        print(f'Subject created/verified: {subject}')

        # -----------------------------
        # 4. Units
        # -----------------------------
        unit_titles = [
            'Introduction to Computer Systems',
            'Input and Output Devices',
            'Storage Devices',
            'Software Fundamentals',
            'Networking Basics',
            'Programming Concepts',
            'Databases',
            'Web Development Basics',
            'Cybersecurity Fundamentals',
            'Algorithms and Problem Solving',
            'Data Structures',
            'Project Work and Revision'
        ]

        units = []
        for idx, title in enumerate(unit_titles, start=1):
            unit, _ = Unit.objects.get_or_create(
                subject=subject,
                number=idx,
                defaults={
                    'title': title,
                    'key_unit_competence': f'Key competence for unit {idx}: {title}',
                    'total_lessons': 5
                }
            )
            units.append(unit)
            print(f'Unit created/verified: {unit}')

        # -----------------------------
        # 5. Teaching Strategies
        # -----------------------------
        free_strategy, _ = TeachingStrategy.objects.get_or_create(
            name='Interactive Lecture',
            defaults={
                'description': 'Free strategy: interactive lecture with questions',
                'is_premium_only': False
            }
        )

        premium_strategy, _ = TeachingStrategy.objects.get_or_create(
            name='Project-Based Learning',
            defaults={
                'description': 'Premium strategy: hands-on project work',
                'is_premium_only': True
            }
        )

        print(f'Strategies created/verified: {free_strategy}, {premium_strategy}')

        # -----------------------------
        # 6. Lessons + Steps
        # -----------------------------
        for unit in units:
            lesson, _ = Lesson.objects.get_or_create(
                unit=unit,
                number=1,
                defaults={
                    'title': f'{unit.title} - Lesson 1',
                    'is_premium': False
                }
            )
            print(f'Lesson created/verified: {lesson}')

            # Free Strategy Steps
            for step_idx in range(1, 4):
                LessonStrategyStep.objects.get_or_create(
                    lesson=lesson,
                    strategy=free_strategy,
                    step_order=step_idx,
                    defaults={
                        'step_title': f'Free Step {step_idx}',
                        'duration_minutes': 10,
                        'teacher_activity': f'Teacher activity for free step {step_idx}',
                        'learner_activity': f'Learner activity for free step {step_idx}'
                    }
                )

            # Premium Strategy Steps
            for step_idx in range(1, 4):
                LessonStrategyStep.objects.get_or_create(
                    lesson=lesson,
                    strategy=premium_strategy,
                    step_order=step_idx,
                    defaults={
                        'step_title': f'Premium Step {step_idx}',
                        'duration_minutes': 15,
                        'teacher_activity': f'Teacher activity for premium step {step_idx}',
                        'learner_activity': f'Learner activity for premium step {step_idx}'
                    }
                )

        print('✅ Full Computer Science curriculum seeded successfully.')