from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import CustomUserCreationForm, LoginForm, RegistroMaterialForm
from .models import UserProfile
from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib.auth.decorators import login_required


def homepage(request):
    return render(request, "reciclAI/homepage.html")


def cadastro(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            # Cria o usuário
            user = form.save()

            # Captura os dados extras do formulário
            cpf_cnpj_data = form.cleaned_data.get("cpf_cnpj")
            telefone_data = form.cleaned_data.get("telefone")
            tipo_usuario_data = form.cleaned_data.get("tipo_usuario") or "GERADOR"

            # Atualiza o UserProfile criado automaticamente pelo sinal
            profile, created = UserProfile.objects.get_or_create(user=user)

            profile.cpf_cnpj = cpf_cnpj_data
            profile.telefone = telefone_data
            profile.tipo_usuario = tipo_usuario_data
            profile.save()

            return redirect("login")
    else:
        form = CustomUserCreationForm()

    context = {"cadastro_form": form}
    return render(request, "reciclAI/cadastro.html", context)


def login(request):

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth.login(request, user)

                profile, created = UserProfile.objects.get_or_create(user=user)
                tipo = profile.tipo_usuario

                if tipo == "RECICLADOR":
                    return redirect("reciclador")
                else:
                    return redirect("gerador")

    else:
        form = LoginForm()

    context = {"login_form": form}
    return render(request, "reciclAI/login.html", context)


@login_required(login_url="login")
def dashboard_reciclador(request):
    return render(request, "reciclAI/dashboard_reciclador.html")


@login_required(login_url="login")
def dashboard_gerador(request):
    return render(request, "reciclAI/dashboard_gerador.html")


def logout(request):

    auth.logout(request)
    return redirect("homepage")


@login_required(login_url="login")
def registrar_material(request):

    if request.method == "POST":
        form = RegistroMaterialForm(request.POST)
        if form.is_valid():
            registro_material = form.save(commit=False)
            registro_material.usuario = request.user

            registro_material.save()
            return redirect("gerador")

    else:
        form = RegistroMaterialForm()

    context = {"material_form": form}
    return render(request, "reciclAI/registro_material.html", context)
