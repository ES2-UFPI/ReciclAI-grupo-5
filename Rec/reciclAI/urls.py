from django.urls import path
from . import views

app_name = "reciclAI"

urlpatterns = [
    # --- Rotas Públicas e de Autenticação ---
    path("", views.public_index, name="public_index"),
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # --- Fluxo do Cidadão ---
    path("cidadao/residuos/", views.residue_list, name="residue_list"),
    path("cidadao/residuos/cadastrar/", views.residue_create, name="residue_create"),
    path("cidadao/coletas/", views.collection_status, name="collection_status"),
    path("cidadao/pontos/", views.points_history, name="points_history"),
    path("cidadao/recompensas/", views.rewards_list, name="rewards_list"),
    path(
        "cidadao/recompensas/<int:reward_id>/resgatar/",
        views.redeem_reward,
        name="redeem_reward",
    ),
    # --- Fluxo do Coletor ---
    path("coletor/dashboard/", views.collector_dashboard, name="collector_dashboard"),
    path(
        "coletor/coletas/<int:collection_id>/aceitar/",
        views.accept_collection,
        name="accept_collection",
    ),
    path(
        "coletor/coletas/<int:collection_id>/transicao/",
        views.collection_transition,
        name="collection_transition",
    ),
    # --- Fluxo da Recicladora ---
    path("recicladora/dashboard/", views.recycler_dashboard, name="recycler_dashboard"),
    path(
        "recicladora/coletas/<int:collection_id>/processar/",
        views.process_collection,
        name="process_collection",
    ),
    path('historico/', views.historico_coletas, name='historico_coletas'),
]
