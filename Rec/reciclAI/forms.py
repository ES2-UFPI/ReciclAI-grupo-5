from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from .models import Profile, Residue, Collection


class CustomUserCreationForm(UserCreationForm):
    # ... (código existente sem alteração)
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
    # ... (código existente sem alteração)
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
    """
    Formulário para o coletor atualizar o status de uma coleta.
    A lógica de transição de status é aplicada aqui.
    """

    # Define as transições de status permitidas
    STATUS_TRANSITIONS = {
        "ATRIBUIDA": [("EM_ROTA", "Em Rota"), ("CANCELADA", "Cancelada")],
        "EM_ROTA": [("COLETADA", "Coletada"), ("CANCELADA", "Cancelada")],
        "COLETADA": [("ENTREGUE_RECICLADORA", "Entregue na Recicladora")],
    }

    def __init__(self, *args, **kwargs):
        current_status = kwargs.pop("current_status", None)
        super().__init__(*args, **kwargs)

        # Filtra as opções do campo 'status' com base no status atual
        if current_status in self.STATUS_TRANSITIONS:
            allowed_choices = self.STATUS_TRANSITIONS[current_status]
            # Adiciona a opção atual para o caso de não querer mudar
            allowed_choices.insert(
                0, (self.instance.status, self.instance.get_status_display())
            )
            self.fields["status"].choices = allowed_choices
        else:
            # Se não houver transições (ex: 'ENTREGUE'), o campo fica desabilitado
            self.fields["status"].disabled = True
            self.fields["status"].help_text = (
                "Esta coleta não pode mais ter seu status alterado."
            )

    class Meta:
        model = Collection
        fields = ["status"]
        labels = {"status": "Atualizar Status da Coleta"}
