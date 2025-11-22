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
def assign_points_on_processing(sender, instance, created, **kwargs):
    """
    Atribui pontos ao cidadão quando a coleta é marcada como 'PROCESSADO'.
    """
    # Verifica se o status da coleta é 'PROCESSADO'
    if instance.status == "PROCESSADO":
        try:
            # Acessa o cidadão através do resíduo associado à coleta
            citizen_profile = instance.residue.citizen.profile

            # Adiciona 1 ponto ao perfil do cidadão
            citizen_profile.points += 1
            citizen_profile.save()

            # Log ou mensagem (opcional)
            print(
                f"1 ponto adicionado a {citizen_profile.user.username}. Total: {citizen_profile.points} pontos."
            )

        except Profile.DoesNotExist:
            # Lida com o caso em que o perfil não existe
            print(
                f"Erro: Perfil para o usuário {instance.residue.citizen.username} não encontrado."
            )
        except Exception as e:
            # Lida com outras exceções inesperadas
            print(f"Ocorreu um erro ao atribuir pontos: {e}")
