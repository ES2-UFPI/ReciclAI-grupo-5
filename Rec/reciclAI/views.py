from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from .models import Residue, Collection, Profile
from .forms import CustomUserCreationForm, ResidueForm, CollectionStatusForm

# --- Views Públicas e de Autenticação ---


def public_index(request):
    if request.user.is_authenticated:
        return redirect("reciclAI:dashboard")
    return render(request, "reciclAI/public_index.html")


@login_required
def dashboard(request):
    user_type = request.user.profile.user_type
    if user_type == "C":
        return redirect("reciclAI:residue_list")
    elif user_type == "L":
        return redirect("reciclAI:collector_dashboard")
    elif user_type == "R":
        return redirect("reciclAI:recycler_dashboard")
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


def collector_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.user_type != "L":
            return HttpResponseForbidden("Acesso negado. Apenas para coletores.")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def recycler_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.user_type != "R":
            return HttpResponseForbidden("Acesso negado. Apenas para recicladoras.")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


# --- Fluxo do Cidadão (Existente) ---
@citizen_required
def residue_list(request):
    residues = Residue.objects.filter(citizen=request.user).order_by("-created_at")
    return render(request, "reciclAI/residue_list.html", {"residues": residues})


@citizen_required
def residue_create(request):
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
    residue = get_object_or_404(Residue, id=residue_id, citizen=request.user)
    if residue.status != "AGUARDANDO_SOLICITACAO_DE_COLETA":
        messages.error(
            request, "Este resíduo já teve sua coleta solicitada ou finalizada."
        )
        return redirect("reciclAI:residue_list")
    Collection.objects.create(residue=residue, status="SOLICITADA")
    residue.status = "COLETA_SOLICITADA"
    residue.save()
    messages.success(request, "Coleta solicitada com sucesso!")
    return redirect("reciclAI:collection_status")


@citizen_required
def collection_status(request):
    collections = Collection.objects.filter(residue__citizen=request.user).order_by(
        "-updated_at"
    )
    return render(
        request, "reciclAI/collection_status.html", {"collections": collections}
    )


# --- Fluxo do Coletor (Existente) ---
@collector_required
def collector_dashboard(request):
    available_collections = Collection.objects.filter(status="SOLICITADA").order_by(
        "created_at"
    )
    my_collections_status = ["ATRIBUIDA", "EM_ROTA", "COLETADA"]
    my_collections = Collection.objects.filter(
        collector=request.user, status__in=my_collections_status
    ).order_by("-updated_at")
    context = {
        "available_collections": available_collections,
        "my_collections": my_collections,
    }
    return render(request, "reciclAI/collector_dashboard.html", context)


@collector_required
@transaction.atomic
def accept_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id, status="SOLICITADA")
    collection.collector = request.user
    collection.status = "ATRIBUIDA"
    collection.save()
    messages.success(
        request,
        f'Coleta do resíduo "{collection.residue.residue_type}" atribuída a você!',
    )
    return redirect("reciclAI:collector_dashboard")


@collector_required
def collection_transition(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    # Garante que apenas o coletor responsável ou um coletor novo (para coletas 'SOLICITADA')
    # possa acessar esta view.
    if collection.status != "SOLICITADA" and collection.collector != request.user:
        messages.error(
            request, "Você não tem permissão para alterar o status desta coleta."
        )
        return redirect("reciclAI:collector_dashboard")

    if request.method == "POST":
        form = CollectionStatusForm(
            request.POST, instance=collection, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Status da coleta atualizado com sucesso.")
            return redirect("reciclAI:collector_dashboard")
    else:
        form = CollectionStatusForm(instance=collection, user=request.user)

    context = {"form": form, "collection": collection}
    return render(request, "reciclAI/collection_transition.html", context)


# --- Fluxo da Recicladora ---


@recycler_required
def recycler_dashboard(request):
    """
    Dashboard da recicladora, mostrando coletas entregues e prontas para processamento.
    """
    collections_to_process = Collection.objects.filter(
        status="ENTREGUE_RECICLADORA"
    ).order_by("updated_at")
    processed_collections = Collection.objects.filter(status="PROCESSADO").order_by(
        "-processed_at"
    )[
        :10
    ]  # Mostra as 10 últimas

    context = {
        "collections_to_process": collections_to_process,
        "processed_collections": processed_collections,
    }
    return render(request, "reciclAI/recycler_dashboard.html", context)


@recycler_required
@transaction.atomic
def process_collection(request, collection_id):
    """
    Exibe os detalhes de uma coleta e permite confirmar o processamento.
    """
    collection = get_object_or_404(
        Collection, id=collection_id, status="ENTREGUE_RECICLADORA"
    )

    if request.method == "POST":
        # Atualiza o status da coleta e do resíduo
        collection.status = "PROCESSADO"
        collection.processed_at = timezone.now()
        collection.save()

        residue = collection.residue
        residue.status = "PROCESSADO"
        residue.save()

        # Futuramente, a lógica de pontos será adicionada aqui
        messages.success(
            request, f'O resíduo "{residue.residue_type}" foi processado com sucesso.'
        )
        return redirect("reciclAI:recycler_dashboard")

    context = {"collection": collection}
    return render(request, "reciclAI/process_collection.html", context)
