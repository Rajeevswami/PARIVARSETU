from django.utils import timezone

from apps.audit import services as audit_services
from apps.common.exceptions import ApplicationError

from ..models import STEPS, OnboardingProgress


def get_progress(user) -> dict:
    progress, _created = OnboardingProgress.objects.get_or_create(user=user)
    steps = {step: bool(progress.steps.get(step)) for step in STEPS}
    if user.family_id and not steps["family"]:
        steps["family"] = True
        progress.steps = steps
        progress.save(update_fields=["steps", "updated_at"])
    pending = [step for step in STEPS if not steps[step]]
    return {
        "steps": steps,
        "next": pending[0] if pending else None,
        "completed": not pending,
    }


def complete_step(*, user, step: str) -> dict:
    if step not in STEPS:
        raise ApplicationError("Unknown onboarding step.", code="unknown_step")
    progress, _created = OnboardingProgress.objects.get_or_create(user=user)
    progress.steps[step] = True
    if all(progress.steps.get(name) for name in STEPS):
        progress.completed_at = timezone.now()
        audit_services.record(
            actor=user,
            action="onboarding_completed",
            target_model="OnboardingProgress",
            target_id=progress.id,
            family_id=user.family_id,
        )
    progress.save(update_fields=["steps", "completed_at", "updated_at"])
    return get_progress(user)
