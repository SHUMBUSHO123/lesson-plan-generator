# File: bulk_upload_units.py

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from lessons.models import Level, Class, Subject, Unit, Lesson


class Command(BaseCommand):
    help = "Strict bulk upload Levels → Classes → Subjects → Units → Lessons (Real Titles)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', type=str, required=True,
            help='Path to CSV or Excel file'
        )
        parser.add_argument(
            '--sheet', type=str, default=None,
            help='Excel sheet name (if applicable)'
        )

    @transaction.atomic
    def handle(self, *args, **options):

        file_path = options['file']
        sheet_name = options['sheet']

        # -------------------------
        # Load File
        # -------------------------
        if file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        elif file_path.endswith('.csv'):
            try:
                df = pd.read_csv(file_path, engine="python", encoding="utf-8")
            except Exception as e:
                raise CommandError(f"CSV parsing failed: {e}")
        else:
            raise CommandError("Unsupported file type. Use CSV or Excel.")

        df.columns = df.columns.str.strip()

        # -------------------------
        # Required Columns
        # -------------------------
        required_cols = [
            'Level', 'Class', 'Subject',
            'Unit Number', 'Unit Title',
            'Key Unit Competence', 'Total Lessons',
            'Lesson Number', 'Lesson Title'
        ]

        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise CommandError(f'Missing required columns: {missing_cols}')

        created_levels = 0
        created_classes = 0
        created_subjects = 0
        created_units = 0
        created_lessons = 0

        # -------------------------
        # Process Each Lesson Row
        # -------------------------
        for idx, row in df.iterrows():

            for col in required_cols:
                if pd.isna(row[col]) or str(row[col]).strip() == '':
                    raise CommandError(
                        f'Row {idx + 2} missing mandatory field: {col}'
                    )

            level_name = str(row['Level']).strip()
            class_name = str(row['Class']).strip()
            subject_name = str(row['Subject']).strip()
            unit_number = int(row['Unit Number'])
            unit_title = str(row['Unit Title']).strip()
            key_unit_competence = str(row['Key Unit Competence']).strip()
            total_lessons = int(row['Total Lessons'])
            lesson_number = int(row['Lesson Number'])
            lesson_title = str(row['Lesson Title']).strip()

            # -------------------------
            # Create Structure
            # -------------------------
            level, level_created = Level.objects.get_or_create(name=level_name)
            if level_created:
                created_levels += 1

            cls, class_created = Class.objects.get_or_create(
                level=level,
                name=class_name
            )
            if class_created:
                created_classes += 1

            subject, subject_created = Subject.objects.get_or_create(
                class_field=cls,
                name=subject_name
            )
            if subject_created:
                created_subjects += 1

            # -------------------------
            # Create or Update Unit
            # -------------------------
            unit, unit_created = Unit.objects.get_or_create(
                subject=subject,
                number=unit_number,
                defaults={
                    'title': unit_title,
                    'key_unit_competence': key_unit_competence,
                    'total_lessons': total_lessons
                }
            )

            if unit_created:
                created_units += 1
            else:
                updated = False
                if unit.title != unit_title:
                    unit.title = unit_title
                    updated = True
                if unit.key_unit_competence != key_unit_competence:
                    unit.key_unit_competence = key_unit_competence
                    updated = True
                if unit.total_lessons != total_lessons:
                    unit.total_lessons = total_lessons
                    updated = True
                if updated:
                    unit.save()

            # -------------------------
            # Create or Update Lesson
            # -------------------------
            lesson, lesson_created = Lesson.objects.update_or_create(
                unit=unit,
                number=lesson_number,
                defaults={
                    'title': lesson_title,
                    'is_premium': True
                }
            )

            if lesson_created:
                created_lessons += 1

        # -------------------------
        # Summary
        # -------------------------
        self.stdout.write(self.style.SUCCESS("✅ Bulk upload complete"))
        self.stdout.write(f"Levels created: {created_levels}")
        self.stdout.write(f"Classes created: {created_classes}")
        self.stdout.write(f"Subjects created: {created_subjects}")
        self.stdout.write(f"Units created: {created_units}")
        self.stdout.write(f"Lessons created: {created_lessons}")
