import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from lessons.models import Level, Class, Subject, Unit, Lesson


class Command(BaseCommand):
    help = "Optimized bulk upload Levels → Classes → Subjects → Units → Lessons"

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
                df = pd.read_csv(file_path, engine="python", encoding="utf-8-sig")
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

        # Drop fully blank rows
        df = df.dropna(how='all')
        df = df[~df.apply(lambda r: all(str(v).strip() == '' for v in r), axis=1)]

        # Validate all rows up front before touching the DB
        for idx, row in df.iterrows():
            for col in required_cols:
                if pd.isna(row[col]) or str(row[col]).strip() == '':
                    raise CommandError(f'Row {idx + 2} missing mandatory field: {col}')

        # Normalize columns
        df['Level']               = df['Level'].astype(str).str.strip()
        df['Class']               = df['Class'].astype(str).str.strip()
        df['Subject']             = df['Subject'].astype(str).str.strip()
        df['Unit Number']         = df['Unit Number'].astype(str).str.replace('Unit', '', case=False).str.strip().astype(int)
        df['Unit Title']          = df['Unit Title'].astype(str).str.strip()
        df['Key Unit Competence'] = df['Key Unit Competence'].astype(str).str.strip()
        df['Total Lessons']       = df['Total Lessons'].astype(str).str.strip().astype(int)
        df['Lesson Number']       = df['Lesson Number'].astype(str).str.replace('Lesson', '', case=False).str.strip().astype(int)
        df['Lesson Title']        = df['Lesson Title'].astype(str).str.strip()

        created_levels   = 0
        created_classes  = 0
        created_subjects = 0
        created_units    = 0
        created_lessons  = 0

        # -------------------------
        # Step 1: Levels (bulk)
        # -------------------------
        self.stdout.write("Processing Levels...")
        level_names = df['Level'].unique()
        existing_levels = {l.name: l for l in Level.objects.filter(name__in=level_names)}

        new_levels = [Level(name=name) for name in level_names if name not in existing_levels]
        if new_levels:
            Level.objects.bulk_create(new_levels)
            created_levels = len(new_levels)

        level_map = {l.name: l for l in Level.objects.filter(name__in=level_names)}

        # -------------------------
        # Step 2: Classes (bulk)
        # -------------------------
        self.stdout.write("Processing Classes...")
        class_keys = df[['Level', 'Class']].drop_duplicates()
        existing_classes = {
            (c.level_id, c.name): c
            for c in Class.objects.filter(level__name__in=level_names)
        }

        new_classes = []
        for _, r in class_keys.iterrows():
            level = level_map[r['Level']]
            if (level.id, r['Class']) not in existing_classes:
                new_classes.append(Class(level=level, name=r['Class']))

        if new_classes:
            Class.objects.bulk_create(new_classes)
            created_classes = len(new_classes)

        class_map = {
            (c.level_id, c.name): c
            for c in Class.objects.filter(level__name__in=level_names)
        }

        # -------------------------
        # Step 3: Subjects (bulk)
        # -------------------------
        self.stdout.write("Processing Subjects...")
        subject_keys = df[['Level', 'Class', 'Subject']].drop_duplicates()
        class_ids = [c.id for c in class_map.values()]
        existing_subjects = {
            (s.class_field_id, s.name): s
            for s in Subject.objects.filter(class_field_id__in=class_ids)
        }

        new_subjects = []
        for _, r in subject_keys.iterrows():
            level = level_map[r['Level']]
            cls = class_map[(level.id, r['Class'])]
            if (cls.id, r['Subject']) not in existing_subjects:
                new_subjects.append(Subject(class_field=cls, name=r['Subject']))

        if new_subjects:
            Subject.objects.bulk_create(new_subjects)
            created_subjects = len(new_subjects)

        subject_map = {
            (s.class_field_id, s.name): s
            for s in Subject.objects.filter(class_field_id__in=class_ids)
        }

        # -------------------------
        # Step 4: Units (bulk)
        # -------------------------
        self.stdout.write("Processing Units...")
        unit_keys = df[['Level', 'Class', 'Subject', 'Unit Number', 'Unit Title', 'Key Unit Competence', 'Total Lessons']].drop_duplicates()
        subject_ids = [s.id for s in subject_map.values()]
        existing_units = {
            (u.subject_id, u.number): u
            for u in Unit.objects.filter(subject_id__in=subject_ids)
        }

        new_units = []
        units_to_update = []

        for _, r in unit_keys.iterrows():
            level = level_map[r['Level']]
            cls = class_map[(level.id, r['Class'])]
            subject = subject_map[(cls.id, r['Subject'])]
            key = (subject.id, r['Unit Number'])

            if key not in existing_units:
                new_units.append(Unit(
                    subject=subject,
                    number=r['Unit Number'],
                    title=r['Unit Title'],
                    key_unit_competence=r['Key Unit Competence'],
                    total_lessons=r['Total Lessons']
                ))
            else:
                unit = existing_units[key]
                changed = False
                if unit.title != r['Unit Title']:
                    unit.title = r['Unit Title']
                    changed = True
                if unit.key_unit_competence != r['Key Unit Competence']:
                    unit.key_unit_competence = r['Key Unit Competence']
                    changed = True
                if unit.total_lessons != r['Total Lessons']:
                    unit.total_lessons = r['Total Lessons']
                    changed = True
                if changed:
                    units_to_update.append(unit)

        if new_units:
            Unit.objects.bulk_create(new_units)
            created_units = len(new_units)

        if units_to_update:
            Unit.objects.bulk_update(units_to_update, ['title', 'key_unit_competence', 'total_lessons'])

        unit_map = {
            (u.subject_id, u.number): u
            for u in Unit.objects.filter(subject_id__in=subject_ids)
        }

        # -------------------------
        # Step 5: Lessons (bulk)
        # -------------------------
        self.stdout.write("Processing Lessons...")
        unit_ids = [u.id for u in unit_map.values()]
        existing_lessons = {
            (l.unit_id, l.number): l
            for l in Lesson.objects.filter(unit_id__in=unit_ids)
        }

        new_lessons = []
        lessons_to_update = []

        for _, r in df.iterrows():
            level = level_map[r['Level']]
            cls = class_map[(level.id, r['Class'])]
            subject = subject_map[(cls.id, r['Subject'])]
            unit = unit_map[(subject.id, r['Unit Number'])]
            key = (unit.id, r['Lesson Number'])

            if key not in existing_lessons:
                new_lessons.append(Lesson(
                    unit=unit,
                    number=r['Lesson Number'],
                    title=r['Lesson Title'],
                    is_premium=True
                ))
            else:
                lesson = existing_lessons[key]
                if lesson.title != r['Lesson Title']:
                    lesson.title = r['Lesson Title']
                    lessons_to_update.append(lesson)

        if new_lessons:
            Lesson.objects.bulk_create(new_lessons)
            created_lessons = len(new_lessons)

        if lessons_to_update:
            Lesson.objects.bulk_update(lessons_to_update, ['title'])

        # -------------------------
        # Summary
        # -------------------------
        self.stdout.write(self.style.SUCCESS("✅ Bulk upload complete"))
        self.stdout.write(f"Levels created:   {created_levels}")
        self.stdout.write(f"Classes created:  {created_classes}")
        self.stdout.write(f"Subjects created: {created_subjects}")
        self.stdout.write(f"Units created:    {created_units}")
        self.stdout.write(f"Lessons created:  {created_lessons}")