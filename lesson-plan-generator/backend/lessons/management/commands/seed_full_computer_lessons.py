from django.core.management.base import BaseCommand
from lessons.models import Level, Class, Subject, Unit, Lesson, TeachingStrategy, LessonStrategyStep

class Command(BaseCommand):
    help = 'Seed full Senior Six Computer Science curriculum with lessons and strategy steps'

    def handle(self, *args, **kwargs):
        print("🔥 Seeding full Senior Six Computer Science curriculum...")

        # -------------------
        # Level, Class, Subject
        # -------------------
        level, _ = Level.objects.get_or_create(name='Senior Six')
        class_field, _ = Class.objects.get_or_create(level=level, name='Computer Science')
        subject, _ = Subject.objects.get_or_create(class_field=class_field, name='Computer Science')

        # -------------------
        # Units
        # -------------------
        units_info = [
            (1, 'Introduction to Computer Systems', 'Understand the basic components of a computer system and their functions'),
            (2, 'Input and Output Devices', 'Identify different input and output devices and their uses'),
            (3, 'Storage Devices', 'Understand primary and secondary storage and their characteristics'),
            (4, 'Software Fundamentals', 'Distinguish system software from application software'),
            (5, 'Networking Basics', 'Understand basic networking concepts and protocols'),
            (6, 'Programming Concepts', 'Understand fundamental programming concepts and structures'),
            (7, 'Databases', 'Understand database fundamentals and data management'),
            (8, 'Web Development Basics', 'Understand web technologies and basic web design'),
            (9, 'Cybersecurity Fundamentals', 'Understand basic cybersecurity principles and threats'),
            (10, 'Algorithms and Problem Solving', 'Develop problem solving skills using algorithms'),
            (11, 'Data Structures', 'Understand different data structures and their applications'),
            (12, 'Project Work and Revision', 'Apply knowledge to a real-life computer science project')
        ]

        units = []
        for number, title, competence in units_info:
            unit, _ = Unit.objects.get_or_create(
                subject=subject,
                number=number,
                defaults={'title': title, 'key_unit_competence': competence, 'total_lessons': 5}
            )
            units.append(unit)
            print(f"Unit created/verified: {subject.name} - Unit {number}: {title}")

        # -------------------
        # Teaching Strategies
        # -------------------
        strategies = [
            {'name': 'Interactive Lecture', 'is_premium_only': False},
            {'name': 'Project-Based Learning', 'is_premium_only': True}
        ]

        strategy_objs = []
        for s in strategies:
            strategy, _ = TeachingStrategy.objects.get_or_create(**s)
            strategy_objs.append(strategy)
            print(f"Strategy created/verified: {strategy.name}")

        # -------------------
        # Lessons and Steps
        # -------------------
        for unit in units:
            for lesson_idx in range(5):  # 5 lessons per unit
                lesson_title = f"{unit.title} - Lesson {lesson_idx + 1}"
                lesson, _ = Lesson.objects.get_or_create(
                    unit=unit,
                    number=lesson_idx + 1,
                    defaults={'title': lesson_title}
                )
                print(f"Lesson created/verified: {lesson.title} - Lesson {lesson.number}")

                # Seed steps for each strategy
                for strategy in strategy_objs:
                    for step_order, step_name in enumerate(['Introduction', 'Development', 'Conclusion'], start=1):
                        step_title = step_name
                        step_defaults = {
                            'step_title': step_title,
                            'duration_minutes': 10,
                            'teacher_activity': f"Teacher activity for {step_name} of {lesson.title}",
                            'learner_activity': f"Learner activity for {step_name} of {lesson.title}",
                            'generic_competence': unit.key_unit_competence
                        }
                        LessonStrategyStep.objects.get_or_create(
                            lesson=lesson,
                            strategy=strategy,
                            step_order=step_order,
                            defaults=step_defaults
                        )
        
        print("✅ Full Senior Six Computer Science curriculum seeded successfully.")
