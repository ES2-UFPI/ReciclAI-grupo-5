from django.urls import path
from . import views

app_name = "reciclAI"

urlpatterns = [
    # --- Rotas Públicas e de Autenticação ---
    path("", views.public_index, name="public_index"),
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # --- Fluxo do Cidadão ---
    # Listar resíduos para solicitar coleta
    path("cidadao/residuos/", views.residue_list, name="residue_list"),
    # Cadastrar um novo resíduo
    path("cidadao/residuos/cadastrar/", views.residue_create, name="residue_create"),
    # Solicitar a coleta de um resíduo
    path(
        "cidadao/residuos/<int:residue_id>/solicitar-coleta/",
        views.request_collection,
        name="request_collection",
    ),
    # Acompanhar o status das coletas
    path("cidadao/coletas/", views.collection_status, name="collection_status"),
    # --- Fluxo do Coletor (Temporariamente Desativado) ---
    # path('coletor/coletas/disponiveis/', views.available_collections, name='available_collections'),
    # path('coletor/coletas/<int:collection_id>/aceitar/', views.accept_collection, name='accept_collection'),
    # path('coletor/coletas/<int:collection_id>/atualizar/', views.update_collection_status, name='update_collection_status'),
    # --- Fluxo da Recicladora (Temporariamente Desativado) ---
    # path('recicladora/recebidos/', views.recycler_received, name='recycler_received'),
    # path('recicladora/processar/<int:residue_id>/', views.recycler_process, name='recycler_process'),
]
