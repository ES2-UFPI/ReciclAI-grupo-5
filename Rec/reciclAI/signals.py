from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria um Profile automaticamente para cada novo User.
    """
    if created:
        Profile.objects.create(user=instance, user_type="C")  # 'C' como padrão


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Salva o Profile associado sempre que o User for salvo.
    """
    instance.profile.save()
