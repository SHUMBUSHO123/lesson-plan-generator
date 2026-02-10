# File: lessons/management/commands/fix_lesson_limit.py
from django.core.management.base import BaseCommand
from lessons.models import UserProfile
from lessons.models import FREE_LESSON_LIMIT

class Command(BaseCommand):
    help = "Set default lesson_limit=3 for all guests and non-premium users with NULL lesson_limit"

    def handle(self, *args, **kwargs):
        users_to_fix = UserProfile.objects.filter(is_premium=False, lesson_limit__isnull=True)
        count = users_to_fix.count()

        for user in users_to_fix:
            user.lesson_limit = FREE_LESSON_LIMIT
            user.save(update_fields=['lesson_limit'])

        self.stdout.write(self.style.SUCCESS(f"✅ Fixed lesson_limit for {count} users."))
