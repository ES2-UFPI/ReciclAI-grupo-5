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
        fields = UserCreationForm.Meta.fields

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Profile.objects.create(
                user=user, user_type=self.cleaned_data.get("user_type")
            )
        return user


class ResidueForm(forms.ModelForm):
    collection_date = forms.DateField(
        label="Data para Coleta (Opcional)",
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )

    class Meta:
        model = Residue
        fields = ["residue_type", "weight", "units", "location", "collection_date"]
        labels = {
            "residue_type": "Tipo de Resíduo",
            "weight": "Peso (kg)",
            "units": "Unidades",
            "location": "Endereço de Coleta",
        }
        help_texts = {
            "weight": "Informe um valor aproximado.",
            "units": "Se aplicável (ex: garrafas PET).",
        }

    def clean(self):
        cleaned_data = super().clean()
        weight = cleaned_data.get("weight")
        units = cleaned_data.get("units")
        if not weight and not units:
            raise forms.ValidationError(
                "Você deve informar o Peso ou as Unidades do resíduo."
            )
        return cleaned_data


class CollectionStatusForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["status"]
        labels = {"status": "Atualizar Status da Coleta"}
