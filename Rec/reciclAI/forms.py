from django import forms
from .models import Collection


class CollectionStatusForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["status"]
