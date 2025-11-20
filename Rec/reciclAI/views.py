from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db import transaction
from django.db.models import F
from django.contrib import messages
from .models import Residue, Collection, Reward, Profile, UserReward
from .forms import CollectionStatusForm, ResidueForm


def index(request):
    return render(request, "reciclAI/index.html")


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # A criação do Profile agora é feita por um signal.
            return redirect("reciclAI:index")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def residue_create(request):
    # Adicionar verificação de perfil de Cidadão
    if request.user.profile.user_type != "C":
        return HttpResponseForbidden("Apenas cidadãos podem registrar resíduos.")
    if request.method == "POST":
        form = ResidueForm(request.POST)
        if form.is_valid():
            residue = form.save(commit=False)
            residue.citizen = request.user
            residue.save()
            Collection.objects.create(residue=residue, status="S")
            messages.success(request, "Seu resíduo foi registrado com sucesso!")
            return redirect("reciclAI:collection_status")
    else:
        form = ResidueForm()
    return render(request, "reciclAI/residue_form.html", {"form": form})


@login_required
def collection_status(request):
    collections = Collection.objects.filter(residue__citizen=request.user)
    return render(
        request, "reciclAI/collection_status.html", {"collections": collections}
    )


@login_required
def points_view(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, "reciclAI/points_view.html", {"profile": profile})


@login_required
def rewards_list(request):
    rewards = Reward.objects.all()
    return render(request, "reciclAI/rewards_list.html", {"rewards": rewards})


@login_required
def redeem_reward(request, reward_id):
    reward = get_object_or_404(Reward, id=reward_id)
    profile = Profile.objects.get(user=request.user)
    if profile.points >= reward.points_required:
        with transaction.atomic():
            profile.points -= reward.points_required
            profile.save()
            UserReward.objects.create(user=request.user, reward=reward)
        messages.success(request, f'Recompensa "{reward.name}" resgatada com sucesso!')
        return redirect("reciclAI:rewards_list")
    else:
        messages.error(request, "Você não tem pontos suficientes para esta recompensa.")
        return redirect("reciclAI:rewards_list")


@login_required
def available_collections(request):
    if request.user.profile.user_type != "L":
        return HttpResponseForbidden(
            "Apenas coletores podem ver as coletas disponíveis."
        )
    collections = Collection.objects.filter(status="S")
    accepted_collections = Collection.objects.filter(
        collector=request.user, status__in=["A", "E", "C"]
    )
    return render(
        request,
        "reciclAI/available_collections.html",
        {
            "available_collections": collections,
            "accepted_collections": accepted_collections,
        },
    )


@login_required
def accept_collection(request, collection_id):
    if request.user.profile.user_type != "L":
        return HttpResponseForbidden("Apenas coletores podem aceitar coletas.")
    collection = get_object_or_404(Collection, id=collection_id, status="S")
    collection.collector = request.user
    collection.status = "A"
    collection.save()
    messages.success(request, "Coleta aceita com sucesso!")
    return redirect("reciclAI:available_collections")


@login_required
def update_collection_status(request, collection_id):
    if request.user.profile.user_type != "L":
        return HttpResponseForbidden(
            "Apenas coletores podem atualizar o status da coleta."
        )
    collection = get_object_or_404(Collection, id=collection_id, collector=request.user)
    if request.method == "POST":
        form = CollectionStatusForm(request.POST, instance=collection)
        if form.is_valid():
            form.save()
            messages.success(request, "Status da coleta atualizado com sucesso!")
            return redirect("reciclAI:available_collections")
    else:
        form = CollectionStatusForm(instance=collection)
    return render(
        request,
        "reciclAI/update_collection_status.html",
        {"form": form, "collection": collection},
    )


@login_required
def recycler_received(request):
    if request.user.profile.user_type != "R":
        return HttpResponseForbidden("Acesso negado.")
    collections = Collection.objects.filter(status="N")
    return render(
        request, "reciclAI/recycler_received.html", {"collections": collections}
    )


@login_required
def recycler_process(request, residue_id):
    if request.user.profile.user_type != "R":
        return HttpResponseForbidden("Acesso negado.")

    residue = get_object_or_404(Residue, id=residue_id)
    collection = get_object_or_404(Collection, residue=residue, status="N")
    profile, _ = Profile.objects.get_or_create(user=residue.citizen)

    if residue.status == "F":
        messages.warning(request, "Este resíduo já foi finalizado anteriormente.")
        return redirect("reciclAI:recycler_received")

    points_to_award = 0
    if residue.weight:
        points_to_award = int(residue.weight * 10)

    try:
        with transaction.atomic():
            profile.points = F("points") + points_to_award
            profile.save()

            residue.status = "F"
            residue.save()

            collection.status = "F"
            collection.save()

        messages.success(
            request,
            f"{points_to_award} pontos foram adicionados ao cidadão {profile.user.username}.",
        )
    except Exception as e:
        messages.error(request, f"Ocorreu um erro ao processar o resíduo: {e}")

    return redirect("reciclAI:recycler_received")
