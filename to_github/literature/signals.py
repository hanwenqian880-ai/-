"""
Signals for literature app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Handle user creation."""
    if created:
        # Set default role for new users
        if not instance.role:
            instance.role = User.Role.MEMBER
            instance.save(update_fields=['role'])