from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.forms.widgets import PasswordInput, TextInput
from django.forms import TextInput, RadioSelect

from .models import UserProfile 

class CustomUserCreationForm(UserCreationForm):
    
    tipo_usuario = forms.ChoiceField(
        choices=UserProfile.TIPO_USUARIO_CHOICES, 
        label='Eu sou...',
        initial='GERADOR', 
        required=True,
        widget=RadioSelect(attrs={'class': 'form-check-input'}) 
    )
    
    
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
        
class LoginForm(AuthenticationForm):

    username = forms.CharField(widget=TextInput())
    password = forms.CharField(widget=PasswordInput())        