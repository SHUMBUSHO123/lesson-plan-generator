# File: /lesson-plan-generator/backend/lessons/management/commands/merge_duplicates.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from lessons.models import Level, Class, Subject, Unit, Lesson


class Command(BaseCommand):
    help = "Merge duplicate Levels, Classes, Subjects in the DB"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("🔹 Starting merge process...")

        # -------------------------
        # Merge duplicate Levels
        # -------------------------
        self.stdout.write("Checking for duplicate Levels...")
        duplicates = Level.objects.values('name').annotate(count_id=Count('id')).filter(count_id__gt=1)
        for dup in duplicates:
            objs = Level.objects.filter(name=dup['name']).order_by('id')
            primary = objs.first()
            for obj in objs[1:]:
                # Move classes to primary level
                obj.class_set.update(level=primary)
                obj.delete()
                self.stdout.write(f"Merged Level '{obj.name}' into '{primary.name}'")
        
        # -------------------------
        # Merge duplicate Classes
        # -------------------------
        self.stdout.write("Checking for duplicate Classes...")
        duplicates = Class.objects.values('level', 'name').annotate(count_id=Count('id')).filter(count_id__gt=1)
        for dup in duplicates:
            objs = Class.objects.filter(level=dup['level'], name=dup['name']).order_by('id')
            primary = objs.first()
            for obj in objs[1:]:
                # Move subjects to primary class
                obj.subject_set.update(class_field=primary)
                obj.delete()
                self.stdout.write(f"Merged Class '{obj.name}' into '{primary.name}'")
        
        # -------------------------
        # Merge duplicate Subjects
        # -------------------------
        self.stdout.write("Checking for duplicate Subjects...")
        duplicates = Subject.objects.values('class_field', 'name').annotate(count_id=Count('id')).filter(count_id__gt=1)
        for dup in duplicates:
            objs = Subject.objects.filter(class_field=dup['class_field'], name=dup['name']).order_by('id')
            primary = objs.first()
            for obj in objs[1:]:
                # Move units to primary subject
                obj.unit_set.update(subject=primary)
                obj.delete()
                self.stdout.write(f"Merged Subject '{obj.name}' into '{primary.name}'")
        
        self.stdout.write(self.style.SUCCESS("✅ Merge complete!"))
