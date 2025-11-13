from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    TIPO_USUARIO_CHOICES = (
        ("GERADOR", "Gerador de Resíduos"),
        ("RECICLADOR", "Reciclador"),
    )

    cpf_cnpj = models.CharField(
        max_length=18,
        unique=True,
        verbose_name="CPF/CNPJ",
        null=True,
        blank=True,
    )

    telefone = models.CharField(max_length=15, null=True, blank=True)

    tipo_usuario = models.CharField(
        max_length=15,
        choices=TIPO_USUARIO_CHOICES,
        default="GERADOR",
        verbose_name="Tipo de Usuário",
    )

    num_moedas = models.IntegerField(default=0)

    def __str__(self):
        return (
            f"Perfil de {self.user.username} - Tipo: {self.get_tipo_usuario_display()}"
        )


class RegistroMaterial(models.Model):

    STATUS_CHOICES = (
        ("PENDENTE", "Aguardando Coleta"),
        ("COLETADO", "Coletado/Concluído"),
        ("CANCELADO", "Cancelado"),
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="materiais",
        verbose_name="Usuário Gerador",
    )

    tipo_material = models.CharField(max_length=50, verbose_name="tipo de material")
    quantidade = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Quantidade (kg, litros, etc.)"
    )

    observacao = models.TextField(
        max_length=500, blank=True, null=True, verbose_name="Observações para o coletor"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="PENDENTE",
        verbose_name="Status da coleta",
    )

    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Material"
        verbose_name_plural = "Registros de Materiais"
        ordering = ["-data_registro"]

    def __str__(self):
        return f"{self.tipo_material} - {self.quantidade} - Status: {self.status} (ID: {self.id})"
