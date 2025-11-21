from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ("C", "Cidadão"),
        ("L", "Coletor"),
        ("R", "Recicladora"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=1, choices=USER_TYPE_CHOICES)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"


class Residue(models.Model):
    STATUS_CHOICES = (
        ("AGUARDANDO_SOLICITACAO_DE_COLETA", "Aguardando Solicitação de Coleta"),
        ("COLETA_SOLICITADA", "Coleta Solicitada"),
        ("PROCESSADO", "Processado"),  # Renomeado para consistência
    )
    citizen = models.ForeignKey(User, on_delete=models.CASCADE)
    residue_type = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    units = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=255)
    collection_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="AGUARDANDO_SOLICITACAO_DE_COLETA",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.residue_type} - {self.citizen.username}"


class Collection(models.Model):
    STATUS_CHOICES = (
        ("SOLICITADA", "Solicitada"),
        ("ATRIBUIDA", "Atribuída"),
        ("EM_ROTA", "Em Rota"),
        ("COLETADA", "Coletada"),
        ("ENTREGUE_RECICLADORA", "Entregue na Recicladora"),
        ("PROCESSADO", "Processado"),  # Novo status
        ("CANCELADA", "Cancelada"),
    )
    residue = models.OneToOneField(Residue, on_delete=models.CASCADE)
    collector = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="SOLICITADA"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)  # Novo campo

    def __str__(self):
        return f"Coleta para {self.residue.residue_type} - Status: {self.get_status_display()}"


class Reward(models.Model):
    name = models.CharField(max_length=100)
    points_required = models.IntegerField()

    def __str__(self):
        return self.name


class UserReward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    date_redeemed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.reward.name}"
