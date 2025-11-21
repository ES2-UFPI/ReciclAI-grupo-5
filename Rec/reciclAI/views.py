from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import transaction
from django.contrib import messages
from .models import Residue, Collection, Profile
from .forms import CustomUserCreationForm, ResidueForm

# --- Views Públicas e de Autenticação ---


def public_index(request):
    if request.user.is_authenticated:
        return redirect("reciclAI:dashboard")
    return render(request, "reciclAI/public_index.html")


@login_required
def dashboard(request):
    user_type = request.user.profile.user_type
    if user_type == "C":
        # Cidadão é direcionado para a lista de resíduos
        return redirect("reciclAI:residue_list")
    elif user_type == "L":
        # Coletor (ainda não implementado no novo fluxo)
        return redirect("reciclAI:available_collections")
    elif user_type == "R":
        # Recicladora (ainda não implementado no novo fluxo)
        return redirect("reciclAI:recycler_received")
    return redirect("login")


def signup(request):
    if request.user.is_authenticated:
        return redirect("reciclAI:dashboard")
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso! Bem-vindo(a).")
            return redirect("reciclAI:dashboard")
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


# --- Decorators de Verificação de Perfil ---


def citizen_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.user_type != "C":
            return HttpResponseForbidden("Acesso negado. Apenas para cidadãos.")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


# --- Fluxo do Cidadão ---


@citizen_required
def residue_list(request):
    """
    Lista os resíduos cadastrados pelo cidadão.
    É a página principal do cidadão, onde ele pode ver o status
    e solicitar a coleta de resíduos que ainda não foram solicitados.
    """
    residues = Residue.objects.filter(citizen=request.user).order_by("-created_at")
    return render(request, "reciclAI/residue_list.html", {"residues": residues})


@citizen_required
def residue_create(request):
    """
    Formulário para o cidadão cadastrar um novo resíduo.
    """
    if request.method == "POST":
        form = ResidueForm(request.POST)
        if form.is_valid():
            residue = form.save(commit=False)
            residue.citizen = request.user
            residue.save()
            messages.success(
                request,
                "Resíduo cadastrado com sucesso! Agora você pode solicitar a coleta.",
            )
            return redirect("reciclAI:residue_list")
    else:
        form = ResidueForm()
    return render(request, "reciclAI/residue_form.html", {"form": form})


@citizen_required
@transaction.atomic
def request_collection(request, residue_id):
    """
    Cria uma solicitação de coleta para um resíduo específico.
    Impede a criação de coletas duplicadas.
    """
    residue = get_object_or_404(Residue, id=residue_id, citizen=request.user)

    if residue.status != "AGUARDANDO_SOLICITACAO_DE_COLETA":
        messages.error(
            request, "Este resíduo já teve sua coleta solicitada ou finalizada."
        )
        return redirect("reciclAI:residue_list")

    # Cria a coleta e atualiza o status do resíduo
    Collection.objects.create(residue=residue, status="SOLICITADA")
    residue.status = "COLETA_SOLICITADA"
    residue.save()

    messages.success(request, "Coleta solicitada com sucesso!")
    return redirect("reciclAI:collection_status")  # Redireciona para o acompanhamento


@citizen_required
def collection_status(request):
    """
    Lista todas as coletas solicitadas pelo cidadão para acompanhamento.
    """
    collections = Collection.objects.filter(residue__citizen=request.user).order_by(
        "-updated_at"
    )
    return render(
        request, "reciclAI/collection_status.html", {"collections": collections}
    )


# --- Views Antigas (Desativadas Temporariamente) ---
# As views de Coletor e Recicladora precisam ser refatoradas
# para se alinharem aos novos status e fluxos.

# @login_required
# def available_collections(request): ...

# @login_required
# def accept_collection(request, collection_id): ...

# @login_required
# def update_collection_status(request, collection_id): ...

# @login_required
# def recycler_received(request): ...

# @login_required
# def recycler_process(request, residue_id): ...
