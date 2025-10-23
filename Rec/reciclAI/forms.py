from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.forms.widgets import PasswordInput, TextInput

from .models import UserProfile 


class CustomUserCreationForm(UserCreationForm):
    
    cpf_cnpj = forms.CharField(
        label='CPF ou CNPJ',
        max_length=18,  
        required=True,
        widget=TextInput(attrs={'placeholder': 'Ex: 000.000.000-00', 'class': 'form-control'})
        
    )

   
    telefone = forms.CharField(
        label='Telefone',
        max_length=15,  
        required=True, 
        widget=TextInput(attrs={'placeholder': 'Ex: (99) 99999-9999', 'class': 'form-control'})
    )

    class Meta:
       
        model = User
        fields = ['username', 'email','password1','password2'] 
        