from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db.models import F
from .models import Residue, Collection, Reward, Profile, UserReward
from .forms import CollectionStatusForm, ResidueForm


def index(request):
    return render(request, "reciclAI/index.html")


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log in the user directly after signup
            login(request, user)
            # Create a profile for the new user
            Profile.objects.create(user=user, user_type="C")
            return redirect("reciclAI:index")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


# Views do Cidadão


@login_required
def residue_create(request):
    if request.method == "POST":
        form = ResidueForm(request.POST)
        if form.is_valid():
            residue = form.save(commit=False)
            residue.citizen = request.user
            residue.save()
            # Automatically create a collection request
            Collection.objects.create(residue=residue, status="S")
            return redirect("reciclAI:collection_status")
    else:
        form = ResidueForm()
    return render(request, "reciclAI/residue_form.html", {"form": form})


@login_required
def collection_request(request):
    # This view might be deprecated if collection is created with residue.
    # For now, it can be used to show residues awaiting collection.
    residues = Residue.objects.filter(citizen=request.user, status="A")
    return render(request, "reciclAI/collection_request.html", {"residues": residues})


@login_required
def collection_status(request):
    # Shows the status of all collections for the logged-in citizen
    collections = Collection.objects.filter(residue__citizen=request.user)
    return render(
        request, "reciclAI/collection_status.html", {"collections": collections}
    )


@login_required
def points_view(request):
    profile, created = Profile.objects.get_or_create(
        user=request.user, defaults={"user_type": "C"}
    )
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
        profile.points -= reward.points_required
        profile.save()
        UserReward.objects.create(user=request.user, reward=reward)
        return redirect("reciclAI:rewards_list")
    else:
        return HttpResponse(
            "<h1>Você não tem pontos suficientes para resgatar esta recompensa.</h1>"
        )


# Views do Coletor


@login_required
def available_collections(request):
    # Shows collections that are "Solicitada" (Requested)
    available_collections = Collection.objects.filter(status="S")
    # Shows collections that are "Atribuída" (Assigned) to the current collector
    accepted_collections = Collection.objects.filter(collector=request.user, status="A")

    context = {
        "available_collections": available_collections,
        "accepted_collections": accepted_collections,
    }
    return render(request, "reciclAI/available_collections.html", context)


@login_required
def accept_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    # Assign the collection to the current user (collector)
    collection.collector = request.user
    collection.status = "A"  # "Atribuída" (Assigned)
    collection.save()
    return redirect("reciclAI:available_collections")


@login_required
def update_collection_status(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id, collector=request.user)
    if request.method == "POST":
        form = CollectionStatusForm(request.POST, instance=collection)
        if form.is_valid():
            form.save()
            return redirect("reciclAI:available_collections")
    else:
        form = CollectionStatusForm(instance=collection)
    return render(
        request,
        "reciclAI/update_collection_status.html",
        {"form": form, "collection": collection},
    )


# Views da Recicladora


@login_required
def recycler_received(request):
    # Shows collections that are "Entregue" (Delivered)
    collections = Collection.objects.filter(status="N")
    return render(
        request, "reciclAI/recycler_received.html", {"collections": collections}
    )


@login_required
def recycler_process(request, residue_id):
    residue = get_object_or_404(Residue, id=residue_id)
    profile, _ = Profile.objects.get_or_create(user=residue.citizen)

    # Prevent giving points twice for the same residue
    if residue.status != "F":
        profile.points = F("points") + 10  # Award points
        profile.save()
        residue.status = "F"  # "Finalizado" (Finalized)
        residue.save()

    return redirect("reciclAI:recycler_received")
