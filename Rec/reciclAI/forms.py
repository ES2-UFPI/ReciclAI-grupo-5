from django import forms
from .models import Collection, Residue


class CollectionStatusForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["status"]


class ResidueForm(forms.ModelForm):
    class Meta:
        model = Residue
        fields = ["residue_type", "weight", "units", "location"]
