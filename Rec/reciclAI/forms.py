from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from .models import Profile, Residue, Collection


class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ("C", "Cidadão"),
        ("L", "Coletor"),
        ("R", "Recicladora"),
    )
    user_type = forms.ChoiceField(
        label="Tipo de Perfil",
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        required=True,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        # Removido 'user_type' daqui, pois não pertence ao modelo User
        fields = UserCreationForm.Meta.fields

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        # O UserCreationForm lida com a hash da senha ao salvar
        if commit:
            user.save()
            # Cria o perfil do usuário com o tipo selecionado
            Profile.objects.create(
                user=user, user_type=self.cleaned_data.get("user_type")
            )
        return user


class ResidueForm(forms.ModelForm):
    class Meta:
        model = Residue
        fields = ["residue_type", "weight", "units", "location"]
        labels = {
            "residue_type": "Tipo de Resíduo",
            "weight": "Peso (kg)",
            "units": "Unidades",
            "location": "Endereço de Coleta",
        }


class CollectionStatusForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["status"]
        labels = {"status": "Atualizar Status da Coleta"}
