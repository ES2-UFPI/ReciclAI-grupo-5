from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Residue, Profile, Collection
from .views import haversine
from decimal import Decimal

# Exemplo de uso:
print(Decimal("0.1") + Decimal("0.2"))
# Saída: 0.3 (exato)

# Comparado ao float embutido:
print(0.1 + 0.2)
# Saída: 0.30000000000000004 (com imprecisão)


class UtilsTestCase(TestCase):
    """Testes para funções utilitárias."""

    def test_haversine_calculation(self):
        """Testa se o cálculo de distância da função haversine está correto."""
        # Coordenadas aproximadas de São Paulo e Rio de Janeiro
        lat1, lon1 = -23.5505, -46.6333  # São Paulo
        lat2, lon2 = -22.9068, -43.1729  # Rio de Janeiro

        distance = haversine(lat1, lon1, lat2, lon2)

        # A distância real é de aproximadamente 358 km.
        # O teste verifica se o valor está numa margem razoável.
        self.assertAlmostEqual(distance, 358, delta=5)


class CitizenFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="citizen", password="password")
        # O profile é criado automaticamente pelo signal, user_type padrão 'C'
        self.client.login(username="citizen", password="password")

    def test_create_residue_and_collection_atomically(self):
        """
        Testa se ao criar um resíduo, uma coleta com coordenadas
        é criada atomicamente.
        """
        post_data = {
            "residue_type": "Garrafa PET",
            "units": 10,
            "latitude": "-5.1136",
            "longitude": "-42.8487",
        }
        response = self.client.post(reverse("reciclAI:residue_create"), post_data)

        # Verifica se o usuário foi redirecionado para a página de status
        self.assertRedirects(response, reverse("reciclAI:collection_status"))

        # Verifica se o resíduo e a coleta foram criados
        self.assertEqual(Residue.objects.count(), 1)
        self.assertEqual(Collection.objects.count(), 1)

        residue = Residue.objects.first()
        collection = Collection.objects.first()

        self.assertEqual(residue.citizen, self.user)
        self.assertEqual(residue.status, "COLETA_SOLICITADA")
        self.assertEqual(collection.residue, residue)
        self.assertEqual(collection.status, "SOLICITADA")
        self.assertEqual(collection.latitude, Decimal("-5.1136"))


class CollectorFlowTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Criar usuário cidadão
        self.citizen_user = User.objects.create_user(
            username="citizen_test", password="password"
        )

        # Criar usuário coletor e fazer login
        self.collector_user = User.objects.create_user(
            username="collector_test", password="password"
        )
        self.collector_user.profile.user_type = "L"
        self.collector_user.profile.save()
        self.client.login(username="collector_test", password="password")

        # Criar duas coletas para teste de ordenação
        residue1 = Residue.objects.create(
            citizen=self.citizen_user, residue_type="Perto"
        )
        self.collection_nearby = Collection.objects.create(
            residue=residue1,
            status="SOLICITADA",
            latitude="-23.5500",
            longitude="-46.6300",  # Perto de SP
        )

        residue2 = Residue.objects.create(
            citizen=self.citizen_user, residue_type="Longe"
        )
        self.collection_far = Collection.objects.create(
            residue=residue2,
            status="SOLICITADA",
            latitude="-22.9000",
            longitude="-43.1700",  # Longe (RJ)
        )

    def test_dashboard_loads_without_location(self):
        """Testa se o dashboard do coletor carrega sem parâmetros de localização."""
        response = self.client.get(reverse("reciclAI:collector_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("available_collections", response.context)
        # Verifica se a ordenação padrão (por data de criação) está correta
        self.assertEqual(
            response.context["available_collections"][0].id, self.collection_nearby.id
        )

    def test_dashboard_sorts_collections_by_distance(self):
        """Testa se o dashboard ordena as coletas pela distância quando a localização é fornecida."""
        # Localização do Coletor (próxima à primeira coleta em SP)
        collector_location = {"lat": "-23.5505", "lon": "-46.6333"}

        response = self.client.get(
            reverse("reciclAI:collector_dashboard"), collector_location
        )
        self.assertEqual(response.status_code, 200)

        sorted_collections = response.context["available_collections"]

        # Verifica se a lista não está vazia e se a primeira coleta é a mais próxima
        self.assertTrue(len(sorted_collections) > 0)
        self.assertEqual(sorted_collections[0].id, self.collection_nearby.id)

        # Verifica se o atributo 'distance' foi adicionado e é um número
        self.assertTrue(hasattr(sorted_collections[0], "distance"))
        self.assertIsInstance(sorted_collections[0].distance, float)
        self.assertLess(sorted_collections[0].distance, sorted_collections[1].distance)

class HistoricoColetasTest(TestCase):
    def setUp(self):
        # Cria um usuário coletor para o teste
        self.user = User.objects.create_user(username='coletor1', password='password123')
        self.client = Client()
        self.client.login(username='coletor1', password='password123')

        # Cria dados fictícios de coleta para testar o rendimento
        Collection.objects.create(coletor=self.user, quantidade=10, valor=50.00, data='2023-10-01')
        Collection.objects.create(coletor=self.user, quantidade=5, valor=25.00, data='2023-10-02')

    def test_acesso_historico_coletas(self):
        """Teste se a página carrega e mostra o rendimento correto"""
        # Tenta acessar a URL (que ainda não criamos)
        response = self.client.get(reverse('historico_coletas'))
        
        # Verifica se o status é 200 (Sucesso)
        self.assertEqual(response.status_code, 200)
        
        # Verifica se o template correto está sendo usado
        self.assertTemplateUsed(response, 'reciclAI/historico_coletas.html')
        
        # Verifica se o contexto contém as coletas e o total
        self.assertIn('coletas', response.context)
        self.assertIn('total_rendimento', response.context)
        
        # Verifica se o cálculo do rendimento está correto (50 + 25 = 75)
        self.assertEqual(response.context['total_rendimento'], 75.00)