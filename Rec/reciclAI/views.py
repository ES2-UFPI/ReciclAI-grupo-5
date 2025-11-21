from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import transaction
from django.contrib import messages
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
        # Temporariamente redirecionando para a mesma view do coletor
        # A ser implementado no próximo passo
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


def collector_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.profile.user_type != "L":
            return HttpResponseForbidden("Acesso negado. Apenas para coletores.")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


# --- Fluxo do Cidadão ---


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


# --- Fluxo do Coletor ---


@collector_required
def collector_dashboard(request):
    """
    Dashboard principal do coletor.
    Mostra coletas disponíveis para aceite e as coletas já atribuídas a ele.
    """
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
    """
    Atribui uma coleta disponível ao coletor logado.
    """
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
def update_collection_status(request, collection_id):
    """
    Permite ao coletor atualizar o status de uma coleta que está sob sua responsabilidade.
    """
    collection = get_object_or_404(Collection, id=collection_id, collector=request.user)

    if request.method == "POST":
        form = CollectionStatusForm(
            request.POST, instance=collection, current_status=collection.status
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Status da coleta atualizado com sucesso.")
            return redirect("reciclAI:collector_dashboard")
    else:
        form = CollectionStatusForm(
            instance=collection, current_status=collection.status
        )

    context = {
        "form": form,
        "collection": collection,
    }
    return render(request, "reciclAI/update_collection_status.html", context)


# --- Fluxo da Recicladora (Ainda não implementado) ---
# @login_required
# def recycler_received(request): ...

# @login_required
# def recycler_process(request, residue_id): ...
