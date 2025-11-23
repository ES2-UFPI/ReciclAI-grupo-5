from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, Collection


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Cria um Profile automaticamente para cada novo User.
    """
    if created:
        # Por padrão, o user_type é 'C' (Cidadão),
        # mas a view de signup pode definir outro tipo.
        if not hasattr(instance, "profile"):
            Profile.objects.create(user=instance, user_type="C")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Salva o Profile associado sempre que o User for salvo.
    """
    # Garante que o perfil exista antes de tentar salvá-lo
    if hasattr(instance, "profile"):
        instance.profile.save()


@receiver(post_save, sender=Collection)
def update_residue_status_on_collection_change(sender, instance, **kwargs):
    """
    Atualiza o status do Residue para corresponder ao da Collection.
    """
    residue = instance.residue
    if instance.status == "PROCESSADO" and residue.status != "PROCESSADO":
        residue.status = "PROCESSADO"
        residue.save()
    elif (
        instance.status
        in ["SOLICITADA", "ATRIBUIDA", "EM_ROTA", "COLETADA", "ENTREGUE_RECICLADORA"]
        and residue.status != "COLETA_SOLICITADA"
    ):
        residue.status = "COLETA_SOLICITADA"
        residue.save()
