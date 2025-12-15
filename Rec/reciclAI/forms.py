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
        fields = UserCreationForm.Meta.fields + ("user_type",)

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=True)
        user.profile.user_type = self.cleaned_data.get("user_type")
        if commit:
            user.profile.save()
        return user


class ResidueForm(forms.ModelForm):
    latitude = forms.DecimalField(
        required=True, widget=forms.HiddenInput(attrs={"required": "true"})
    )
    longitude = forms.DecimalField(
        required=True, widget=forms.HiddenInput(attrs={"required": "true"})
    )

    class Meta:
        model = Residue
        fields = ["residue_type", "weight", "units", "latitude", "longitude"]
        labels = {
            "residue_type": "Tipo de Resíduo",
            "weight": "Peso (kg)",
            "units": "Unidades",
        }
        help_texts = {
            "weight": "Informe um valor aproximado.",
            "units": "Se aplicável (ex: garrafas PET).",
        }

    def clean(self):
        cleaned_data = super().clean()
        weight = cleaned_data.get("weight")
        units = cleaned_data.get("units")
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")

        if not weight and not units:
            raise forms.ValidationError(
                "Você deve informar o Peso ou as Unidades do resíduo."
            )

        if weight is not None and weight <= 0:
            self.add_error("weight", "O peso deve ser um valor maior que zero.")

        if units is not None and units <= 0:
            self.add_error("units", "A quantidade de unidades deve ser maior que zero.")

        if not latitude or not longitude:
            raise forms.ValidationError(
                "Você deve selecionar um ponto no mapa para a coleta."
            )

        return cleaned_data


class CollectionStatusForm(forms.ModelForm):
    STATUS_TRANSITIONS = {
        "SOLICITADA": [("ATRIBUIDA", "Atribuir a mim")],
        "ATRIBUIDA": [
            ("EM_ROTA", "Iniciar Rota de Coleta"),
            ("CANCELADA", "Cancelar Coleta"),
        ],
        "EM_ROTA": [("COLETADA", "Marcar como Coletada")],
        "COLETADA": [("ENTREGUE_RECICLADORA", "Marcar como Entregue na Recicladora")],
        "ENTREGUE_RECICLADORA": [],  # Nenhum status seguinte
        "PROCESSADO": [],  # Nenhum status seguinte
        "CANCELADA": [],  # Nenhum status seguinte
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        current_status = self.instance.status

        allowed_transitions = self.STATUS_TRANSITIONS.get(current_status, [])

        if allowed_transitions:
            self.fields["status"].choices = [
                (
                    self.instance.status,
                    f"Manter como {self.instance.get_status_display()}",
                )
            ] + allowed_transitions
            self.fields["status"].help_text = (
                "Selecione o próximo status para a coleta."
            )
        else:
            self.fields["status"].disabled = True
            self.fields["status"].choices = [
                (current_status, self.instance.get_status_display())
            ]
            self.fields["status"].help_text = (
                "Esta coleta não pode mais ter seu status alterado por você."
            )

    def clean_status(self):
        current_status = self.instance.status
        next_status = self.cleaned_data.get("status")

        allowed_transitions = [
            status[0] for status in self.STATUS_TRANSITIONS.get(current_status, [])
        ]

        if next_status == current_status:
            return next_status

        if next_status not in allowed_transitions:
            raise forms.ValidationError(
                f"Transição de status inválida de '{current_status}' para '{next_status}'."
            )

        return next_status

    def save(self, commit=True):
        if (
            self.instance.status == "SOLICITADA"
            and self.cleaned_data.get("status") == "ATRIBUIDA"
        ):
            self.instance.collector = self.user

        return super().save(commit)

    class Meta:
        model = Collection
        fields = ["status"]
        labels = {"status": "Atualizar Status da Coleta"}
