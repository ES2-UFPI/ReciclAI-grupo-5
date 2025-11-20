from django.db import models
from django.contrib.auth.models import User


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
        ("A", "Aguardando Coleta"),
        ("C", "Coletado"),
        ("F", "Finalizado"),
    )
    citizen = models.ForeignKey(User, on_delete=models.CASCADE)
    residue_type = models.CharField(max_length=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    units = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="A")

    def __str__(self):
        return f"{self.residue_type} - {self.citizen.username}"


class Collection(models.Model):
    STATUS_CHOICES = (
        ("S", "Solicitada"),
        ("A", "Atribuída"),
        ("E", "Em rota"),
        ("C", "Coletada"),
        ("N", "Entregue"),
        ("F", "Finalizada"),
        ("X", "Cancelada"),
    )
    residue = models.ForeignKey(Residue, on_delete=models.CASCADE)
    collector = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="S")

    def __str__(self):
        return f"{self.residue} - {self.get_status_display()}"


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
