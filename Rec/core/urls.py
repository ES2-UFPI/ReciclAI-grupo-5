from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("signup/", views.signup, name="signup"),
    # URLs do Cidadão
    path("residue/create/", views.residue_create, name="residue_create"),
    path("collection/request/", views.collection_request, name="collection_request"),
    path("collection/status/", views.collection_status, name="collection_status"),
    path("points/", views.points_view, name="points_view"),
    path("rewards/", views.rewards_list, name="rewards_list"),
    path("rewards/redeem/<int:reward_id>/", views.redeem_reward, name="redeem_reward"),
    # URLs do Coletor
    path(
        "collections/available/",
        views.available_collections,
        name="available_collections",
    ),
    path(
        "collection/accept/<int:collection_id>/",
        views.accept_collection,
        name="accept_collection",
    ),
    path(
        "collection/update_status/<int:collection_id>/",
        views.update_collection_status,
        name="update_collection_status",
    ),
    # URLs da Recicladora
    path("recycler/received/", views.recycler_received, name="recycler_received"),
    path(
        "recycler/process/<int:residue_id>/",
        views.recycler_process,
        name="recycler_process",
    ),
]
