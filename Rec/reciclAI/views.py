from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from .models import Residue, Collection, Profile, PointsTransaction, Reward, UserReward
from .forms import CustomUserCreationForm, ResidueForm, CollectionStatusForm
from django.db.models import F
from math import radians, sin, cos, sqrt, atan2

# --- Função Auxiliar de Geolocalização ---


def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula a distância em quilômetros entre duas coordenadas
    geográficas usando a fórmula de Haversine.
    """
    R = 6371  # Raio da Terra em quilômetros

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


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
    residues = (
        Residue.objects.filter(citizen=request.user)
        .select_related("collection")
        .order_by("-created_at")
    )
    return render(request, "reciclAI/residue_list.html", {"residues": residues})


@citizen_required
@transaction.atomic
def residue_create(request):
    if request.method == "POST":
        form = ResidueForm(request.POST)
        if form.is_valid():
            residue = form.save(commit=False)
            residue.citizen = request.user
            residue.status = "COLETA_SOLICITADA"
            residue.save()

            Collection.objects.create(
                residue=residue,
                status="SOLICITADA",
                latitude=form.cleaned_data["latitude"],
                longitude=form.cleaned_data["longitude"],
            )

            messages.success(
                request, "Sua solicitação de coleta foi registrada com sucesso!"
            )
            return redirect("reciclAI:collection_status")
    else:
        form = ResidueForm()

    return render(request, "reciclAI/residue_form.html", {"form": form})


@citizen_required
def collection_status(request):
    collections = Collection.objects.filter(residue__citizen=request.user).order_by(
        "-updated_at"
    )
    return render(
        request, "reciclAI/collection_status.html", {"collections": collections}
    )


@citizen_required
def points_history(request):
    profile = request.user.profile
    transactions = PointsTransaction.objects.filter(user=request.user).order_by(
        "-transaction_date"
    )

    context = {
        "profile": profile,
        "transactions": transactions,
    }
    return render(request, "reciclAI/points_history.html", context)


# --- Sistema de Recompensas ---
@citizen_required
def rewards_list(request):
    rewards = Reward.objects.filter(is_active=True).order_by("points_required")
    user_points = request.user.profile.points
    context = {
        "rewards": rewards,
        "user_points": user_points,
    }
    return render(request, "reciclAI/rewards_list.html", context)


@citizen_required
@transaction.atomic
def redeem_reward(request, reward_id):
    reward = get_object_or_404(Reward, id=reward_id, is_active=True)
    profile = request.user.profile

    if profile.points >= reward.points_required:
        profile.points -= reward.points_required
        profile.save()

        UserReward.objects.create(user=request.user, reward=reward)

        PointsTransaction.objects.create(
            user=request.user,
            points_gained=-reward.points_required,
            description=f"Resgate da recompensa: {reward.name}",
        )

        messages.success(
            request, f'Parabéns! Você resgatou a recompensa "{reward.name}".'
        )
    else:
        messages.error(
            request, "Você não tem pontos suficientes para resgatar esta recompensa."
        )

    return redirect("reciclAI:rewards_list")


# --- Fluxo do Coletor (Existente) ---
@collector_required
def collector_dashboard(request):
    available_collections = list(
        Collection.objects.filter(
            status="SOLICITADA", latitude__isnull=False, longitude__isnull=False
        ).order_by("created_at")
    )

    collector_lat = request.GET.get("lat")
    collector_lon = request.GET.get("lon")

    if collector_lat and collector_lon:
        try:
            collector_lat = float(collector_lat)
            collector_lon = float(collector_lon)

            for collection in available_collections:
                collection.distance = haversine(
                    collector_lat,
                    collector_lon,
                    float(collection.latitude),
                    float(collection.longitude),
                )

            available_collections.sort(key=lambda c: c.distance)

        except (ValueError, TypeError):
            messages.warning(
                request,
                "Não foi possível processar sua localização. As coletas são exibidas por data.",
            )

    my_collections_status = ["ATRIBUIDA", "EM_ROTA", "COLETADA"]
    my_collections = Collection.objects.filter(
        collector=request.user, status__in=my_collections_status
    ).order_by("-updated_at")

    context = {
        "available_collections": available_collections,
        "my_collections": my_collections,
        "location_shared": bool(collector_lat and collector_lon),
    }
    return render(request, "reciclAI/collector_dashboard.html", context)


@collector_required
@transaction.atomic
def accept_collection(request, collection_id):
    if request.method != "POST":
        return HttpResponseForbidden("Acesso negado.")

    collection = get_object_or_404(Collection, id=collection_id)

    if collection.status != "SOLICITTA":
        messages.error(request, "Esta coleta não está mais disponível.")
        return redirect("reciclAI:collector_dashboard")

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
    collections_to_process = Collection.objects.filter(
        status="ENTREGUE_RECICLADORA"
    ).order_by("updated_at")
    processed_collections = Collection.objects.filter(status="PROCESSADO").order_by(
        "-processed_at"
    )[:10]

    context = {
        "collections_to_process": collections_to_process,
        "processed_collections": processed_collections,
    }
    return render(request, "reciclAI/recycler_dashboard.html", context)


@recycler_required
@transaction.atomic
def process_collection(request, collection_id):
    collection = get_object_or_404(
        Collection.objects.select_related("residue__citizen__profile"),
        id=collection_id,
        status="ENTREGUE_RECICLADORA",
    )

    if request.method == "POST":
        residue = collection.residue
        citizen_profile = residue.citizen.profile

        points_to_award = 10

        citizen_profile.points += points_to_award

        PointsTransaction.objects.create(
            user=residue.citizen,
            points_gained=points_to_award,
            description=f"Coleta de {residue.residue_type} processada.",
        )

        collection.status = "PROCESSADO"
        collection.processed_at = timezone.now()

        collection.save()
        citizen_profile.save()

        messages.success(
            request,
            f'O resíduo "{residue.residue_type}" foi processado e {points_to_award} pontos foram concedidos ao cidadão.',
        )
        return redirect("reciclAI:recycler_dashboard")

    context = {"collection": collection}
    return render(request, "reciclAI/process_collection.html", context)
