# lessons/utils/resolve_profile.py

import uuid
from lessons.models import UserProfile


def resolve_profile(request):
    """
    Single authoritative identity resolver.
    ALWAYS returns a UserProfile.
    """

    # 1️⃣ Logged-in user → authoritative profile
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.device_id:
            profile.device_id = str(uuid.uuid4())
            profile.save(update_fields=["device_id"])
        return profile

    # 2️⃣ Guest user → device-based profile
    device_id = (
        request.data.get("device_id")
        or request.GET.get("device_id")
        or request.session.get("device_id")
    )

    if device_id:
        profile, created = UserProfile.objects.get_or_create(
            device_id=device_id,
            defaults={"user": None}
        )
    else:
        # Generate a new device_id for true new guests
        device_id = str(uuid.uuid4())
        profile = UserProfile.objects.create(device_id=device_id, user=None)

    # Persist device_id in session
    request.session["device_id"] = profile.device_id

    return profile
