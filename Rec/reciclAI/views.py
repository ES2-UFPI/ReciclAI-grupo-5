from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import CustomUserCreationForm
from .models import UserProfile 

def homepage(request):
    return render(request, 'reciclAI/homepage.html')

def cadastro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            
            user = form.save()

            cpf_cnpj_data = form.cleaned_data.get('cpf_cnpj')
            telefone_data = form.cleaned_data.get('telefone')
            
            tipo_usuario_data = form.cleaned_data.get('tipo_usuario', None) 
            profile = UserProfile.objects.create(
                user=user,
                cpf_cnpj=cpf_cnpj_data,
                telefone=telefone_data,
                tipo_usuario=tipo_usuario_data if tipo_usuario_data else 'GERADOR',
          
            )
            
            return redirect('homepage')        
        
    else:
        form = CustomUserCreationForm()
    
    context = {'cadastro_form': form}
    return render(request, 'reciclAI/cadastro.html', context)